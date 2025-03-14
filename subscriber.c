#include <stdio.h>
#include <wiringPi.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>

#define TURN_ON(pin) digitalWrite(pin, HIGH)
#define TURN_OFF(pin) digitalWrite(pin, LOW)

#define READ(pin) digitalRead(pin)
#define WRITE(pin, x) digitalWrite(pin, x)

#define LOW 0
#define HIGH 1

#define PIN_MOTION 4    // Motion sensor
#define PIN_BUZZER 13   // Passive Buzzer
#define PIN_LED_RED 27  // RGB LED Red
#define PIN_LED_GRN 28  // RGB LED Green
#define PIN_LED_BLU 29  // RGB LED Blue
#define PIN_FAN 21      // Fan control pin (connected to transistor base)

#define TEMP_FLAG_PIPE "/tmp/temperature_flag_pipe"

void init_pins() {
    wiringPiSetup(); 

    pinMode(PIN_MOTION, INPUT);
    pinMode(PIN_BUZZER, OUTPUT);
    pinMode(PIN_LED_RED, OUTPUT);
    pinMode(PIN_LED_GRN, OUTPUT);
    pinMode(PIN_LED_BLU, OUTPUT);
    pinMode(PIN_FAN, OUTPUT);  

    TURN_OFF(PIN_BUZZER);
    TURN_OFF(PIN_LED_RED);
    TURN_OFF(PIN_LED_GRN);
    TURN_OFF(PIN_LED_BLU);
    TURN_OFF(PIN_FAN);
}
void cleanup_pins() {
    printf("Cleaning up GPIO pins...\n");
    TURN_OFF(PIN_BUZZER);
    TURN_OFF(PIN_LED_RED);
    TURN_OFF(PIN_LED_GRN);
    TURN_OFF(PIN_LED_BLU);
    TURN_OFF(PIN_FAN);

    pinMode(PIN_BUZZER, INPUT);
    pinMode(PIN_LED_RED, INPUT);
    pinMode(PIN_LED_GRN, INPUT);
    pinMode(PIN_LED_BLU, INPUT);
    pinMode(PIN_FAN, INPUT);
}

void handle_signal(int signal) {
    printf("Received signal %d. Cleaning up...\n", signal);
    cleanup_pins();
    exit(0);
}

int read_temperature_flag() {
    FILE *pipe = fopen(TEMP_FLAG_PIPE, "r");
    if (pipe == NULL) {
        printf("Failed to open temperature flag pipe.\n");
        return 0;  
    }

    int flag;
    fscanf(pipe, "%d", &flag);
    fclose(pipe);

    return flag;
}

void handle_motion() {
    if (READ(PIN_MOTION) == HIGH) {
        printf("Motion detected! Turning on buzzer, FAN, and GREEN LED\n");

        for (int i = 0; i < 3; i++) {
            TURN_ON(PIN_BUZZER);
            delay(200);
            TURN_OFF(PIN_BUZZER);
            delay(200);
        }

        TURN_OFF(PIN_LED_RED);
        TURN_ON(PIN_LED_GRN);
        TURN_OFF(PIN_LED_BLU);
    } else {
        printf("No motion detected. Turning off buzzer, FAN, and setting LED to RED\n");

        TURN_OFF(PIN_BUZZER);

        TURN_ON(PIN_LED_RED);
        TURN_OFF(PIN_LED_GRN);
        TURN_OFF(PIN_LED_BLU);
    }
}

int main() {
    signal(SIGINT, handle_signal); 
    signal(SIGTERM, handle_signal); 

    init_pins();
    printf("System initialized. Monitoring for motion and temperature...\n");

    while (1) {
        int temperature_flag = read_temperature_flag();

        if (temperature_flag == 1) {
            printf("Temperature is above 19C. Monitoring temperature flag...\n");
            TURN_ON(PIN_FAN);
        }
        else {
            printf("Temperature is within range, turning off the fan...\n");
            TURN_OFF(PIN_FAN);
        }
        handle_motion();

        delay(2000);  
    }

    return 0;
}
