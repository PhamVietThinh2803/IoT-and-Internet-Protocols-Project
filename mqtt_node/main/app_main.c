#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#include "driver/gpio.h"
#include "esp_wifi.h"
#include "esp_system.h"
#include "nvs_flash.h"
#include "esp_event.h"
#include "esp_netif.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "freertos/queue.h"
#include "freertos/event_groups.h"

#include "lwip/sockets.h"
#include "lwip/dns.h"
#include "lwip/netdb.h"
#include "lwip/err.h"
#include "lwip/sys.h"

#include "esp_log.h"
#include "mqtt_client.h"

#include "cJSON.h"


#define BLINK_GPIO 2
/* The event group allows multiple bits for each event, but we only care about two events:
 * - connected to the AP with an IP
 * - failed to connect after the maximum amount of retries 
 * - connected to the MQTT Broker*/
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1
#define MQTT_CONNECTED_BIT BIT0

/* FreeRTOS event group to signal when we are connected*/
static EventGroupHandle_t wifi_event_group;
static EventGroupHandle_t mqtt_event_group;
/* Logging tag and variable */
static const char *TAG_MQTT = "MQTT TASK";
static const char *TAG_WIFI = "WIFI TASK";
static int retry_num = 0;
/* Client/Server SSL key and certificate */
extern const uint8_t client_cert_pem_start[] asm("_binary_client_crt_start");
extern const uint8_t client_cert_pem_end[] asm("_binary_client_crt_end");
extern const uint8_t client_key_pem_start[] asm("_binary_client_key_start");
extern const uint8_t client_key_pem_end[] asm("_binary_client_key_end");
extern const uint8_t server_cert_pem_start[] asm("_binary_mosquitto_org_crt_start");
extern const uint8_t server_cert_pem_end[] asm("_binary_mosquitto_org_crt_end");

static void wifi_event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data){
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START){
        ESP_LOGI(TAG_WIFI, "connecting to AP ...");
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED){
        if (retry_num < CONFIG_EXAMPLE_WIFI_CONN_MAX_RETRY) {
            esp_wifi_connect();
            retry_num++;
            ESP_LOGI(TAG_WIFI, "retry to connect to the AP");
        } else {
            xEventGroupSetBits(wifi_event_group, WIFI_FAIL_BIT);
            xEventGroupClearBits(wifi_event_group, WIFI_CONNECTED_BIT);
            ESP_LOGI(TAG_WIFI, "failed to connect to the AP, please reboot the device");
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP){
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG_WIFI, "Got AP IP:" IPSTR, IP2STR(&event->ip_info.ip));
        retry_num = 0;
        xEventGroupSetBits(wifi_event_group, WIFI_CONNECTED_BIT);
        xEventGroupClearBits(wifi_event_group, WIFI_FAIL_BIT);
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_CONNECTED){
        ESP_LOGI(TAG_WIFI, "Connected to AP");
    }
}

void wifi_init(void){
    wifi_event_group = xEventGroupCreate();

    ESP_ERROR_CHECK(esp_netif_init());      // Initialize the underlying TCP/IP stack.
    esp_netif_create_default_wifi_sta();    // Creates default WIFI STASTION

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();    // Default initilize
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    /* Register event handler for WiFi and IP event */
    // esp_err_t esp_event_handler_instance_register(esp_event_base_t event_base, int32_t event_id, esp_event_handler_t event_handler, 
    //                                               void *event_handler_arg, esp_event_handler_instance_t *instance) 
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL, &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL, &instance_got_ip));

    wifi_config_t wifi_config = {
        .sta = {
            .ssid = CONFIG_EXAMPLE_WIFI_SSID,
            .password = CONFIG_EXAMPLE_WIFI_PASSWORD,
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG_WIFI, "Finish initialize WiFi Station");

    /* Waiting until either the connection is established (WIFI_CONNECTED_BIT) or connection failed for the maximum
     * number of re-tries (WIFI_FAIL_BIT). The bits are set by event_handler() (see above) */
    EventBits_t bits = xEventGroupWaitBits(wifi_event_group, WIFI_CONNECTED_BIT | WIFI_FAIL_BIT, pdFALSE, pdFALSE, portMAX_DELAY);
    /* xEventGroupWaitBits() returns the bits before the call returned, hence we can test which event actually happened. */
    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG_WIFI, "connected to AP with SSID: %s", CONFIG_EXAMPLE_WIFI_SSID);
    } else if (bits & WIFI_FAIL_BIT) {
        ESP_LOGI(TAG_WIFI, "Failed to connect to AP with SSID: %s", CONFIG_EXAMPLE_WIFI_SSID);
    } else {
        ESP_LOGE(TAG_WIFI, "UNEXPECTED EVENT!");
    }
}

/*
 * @brief Event handler registered to receive MQTT events
 *
 *  This function is called by the MQTT client event loop.
 *
 * @param handler_args user data registered to the event.
 * @param base Event base for the handler(always MQTT Base in this example).
 * @param event_id The id for the received event.
 * @param event_data The data for the event, esp_mqtt_event_handle_t.
 */

static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data){
    esp_mqtt_event_handle_t event = event_data;
    esp_mqtt_client_handle_t client = event->client;
    int msg_id;
    switch ((esp_mqtt_event_id_t)event_id) {
    case MQTT_EVENT_CONNECTED: // The client has successfully established a connection to the broker
        ESP_LOGI(TAG_MQTT, "MQTT_EVENT_CONNECTED");
        xEventGroupSetBits(mqtt_event_group, MQTT_CONNECTED_BIT);

        msg_id = esp_mqtt_client_publish(client, "ESP32/data", "MQTT node has been connected!", 0, 1, 0);
        ESP_LOGI(TAG_MQTT, "sent publish successful, msg_id = %d", msg_id);
        msg_id = esp_mqtt_client_subscribe(client, "ESP32/command", 0);
        ESP_LOGI(TAG_MQTT, "sent subscribe successful, msg_id = %d", msg_id);
        break;

    case MQTT_EVENT_DISCONNECTED: // The client has aborted the connection due to being unable to read or write data
        ESP_LOGI(TAG_MQTT, "MQTT_EVENT_DISCONNECTED");
        ESP_LOGI(TAG_MQTT, "HOME CENTER MAY HAS BEEN DISCONNECTED TO THE BROKER!");
        xEventGroupClearBits(mqtt_event_group, MQTT_CONNECTED_BIT);
        break;

    case MQTT_EVENT_SUBSCRIBED: // The broker has acknowledged the client’s subscribe request.
        ESP_LOGI(TAG_MQTT, "MQTT_EVENT_SUBSCRIBED: successful. msg_id = %d", event->msg_id);
        break;

    case MQTT_EVENT_UNSUBSCRIBED: // The broker has acknowledged the client’s unsubscribe request.
        ESP_LOGI(TAG_MQTT, "MQTT_EVENT_UNSUBSCRIBED: successful, msg_id=%d", event->msg_id);
        break;

    case MQTT_EVENT_PUBLISHED: // The broker has acknowledged the client’s publish message
        ESP_LOGI(TAG_MQTT, "MQTT_EVENT_PUBLISHED: successful. msg_id = %d", event->msg_id);
        break;

    case MQTT_EVENT_DATA: // The client has received a publish message.
        ESP_LOGI(TAG_MQTT, "MQTT_EVENT_DATA");
        printf("TOPIC = %.*s\r\n", event->topic_len, event->topic);
        printf("DATA = %.*s\r\n", event->data_len, event->data);
        ESP_LOGI(TAG_MQTT, "Free memory after recieving: %d bytes", esp_get_free_heap_size());

        if (strncmp((event->topic), "ESP32/command" , event->topic_len) == 0){
            if(strncmp((event->data), "data" , event->data_len) == 0){  
                char* response_message = NULL;
                cJSON *data = cJSON_CreateObject();
                cJSON *temperature = NULL;
                cJSON *humidity = NULL;
                temperature = cJSON_CreateNumber(rand() % 21 + 20);
                cJSON_AddItemToObject(data, "temperature", temperature);
                humidity = cJSON_CreateNumber(rand() % 31 + 60);
                cJSON_AddItemToObject(data, "humidity", humidity);
                response_message = cJSON_Print(data);
                cJSON_Delete(data);

                msg_id = esp_mqtt_client_publish(client, "ESP32/data", response_message, 0, 1, 0);
                ESP_LOGI(TAG_MQTT, "sent data successful, msg_id = %d", msg_id);

                free(response_message);
            } else if (strncmp((event->data), "On" , event->data_len) == 0){
                ESP_LOGI(TAG_MQTT, "Set power ON! msg_id = %d", event->msg_id);
                gpio_set_level(BLINK_GPIO, 1);
            } else if (strncmp((event->data), "Off" , event->data_len) == 0){
                ESP_LOGI(TAG_MQTT, "Set power OFF! msg_id = %d", event->msg_id);
                gpio_set_level(BLINK_GPIO, 0);
            } 
        }
        break;

    case MQTT_EVENT_ERROR: // The client has encountered an error
        ESP_LOGI(TAG_MQTT, "MQTT_EVENT_ERROR");
        break;

    default:
        ESP_LOGI(TAG_MQTT, "OTHER EVENT, ID: %d", event->event_id);
        break;
    }
}

static void mqtt_app_start(void){
    mqtt_event_group = xEventGroupCreate();
    const esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = CONFIG_BROKER_URL,
        .broker.verification.certificate = (const char *)server_cert_pem_start,
        .credentials = {
            .authentication = {
                .certificate = (const char *)client_cert_pem_start,
                .key = (const char *)client_key_pem_start,
            },
        }
  };
    esp_mqtt_client_handle_t client = esp_mqtt_client_init(&mqtt_cfg);
    /* Registers MQTT event.
    esp_err_t esp_mqtt_client_register_event(esp_mqtt_client_handle_t client, esp_mqtt_event_id_t event, 
                                            esp_event_handler_t event_handler, void *event_handler_arg) */
    esp_mqtt_client_register_event(client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    /* Starts MQTT client with already created client handle. */
    esp_mqtt_client_start(client);
}

void app_main(void){
    ESP_LOGI(TAG_WIFI, "[APP] Startup..");
    ESP_LOGI(TAG_WIFI, "[APP] Free memory: %" PRIu32 " bytes", esp_get_free_heap_size());

    esp_log_level_set("*", ESP_LOG_INFO);
    esp_log_level_set("mqtt_client", ESP_LOG_VERBOSE);
    esp_log_level_set("MQTT TASK", ESP_LOG_VERBOSE);
    esp_log_level_set("TRANSPORT_BASE", ESP_LOG_VERBOSE);
    esp_log_level_set("esp-tls", ESP_LOG_VERBOSE);
    esp_log_level_set("TRANSPORT", ESP_LOG_VERBOSE);
    esp_log_level_set("outbox", ESP_LOG_VERBOSE);

    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    
    /* This helper function configures Wi-Fi or Ethernet, as selected in menuconfig.
     * Read "Establishing Wi-Fi or Ethernet Connection" section in
     * examples/protocols/README.md for more information about this function.
     */
    esp_rom_gpio_pad_select_gpio(BLINK_GPIO);
    gpio_set_direction(BLINK_GPIO, GPIO_MODE_OUTPUT);
    srand(time(0));
    wifi_init();
    mqtt_app_start();
}
