#include <Arduino.h>
#include <driver/gpio.h>
#include <esp_timer.h>

// PlatformIO version of the minimal ESP32 trigger jig.
//
// CH1: direct pulse bursts for PULSe trigger validation.
// CH2: square wave intended to feed an external RC edge shaper for SLOPe tests.
// CH3: optional frame marker pulse at the start of each CH1 burst.

static constexpr gpio_num_t PIN_CH1_DIRECT = GPIO_NUM_18;
static constexpr gpio_num_t PIN_CH2_SLOPE = GPIO_NUM_19;
static constexpr gpio_num_t PIN_CH3_MARKER = GPIO_NUM_21;
static constexpr uint8_t CH2_SLOPE_PWM_CHANNEL = 0;
static constexpr uint8_t CH2_SLOPE_PWM_BITS = 8;
static constexpr uint32_t CH2_SLOPE_PWM_DUTY = 1U << (CH2_SLOPE_PWM_BITS - 1);

static const uint32_t BURST_WIDTHS_US[] = {10, 50, 100, 1000};

volatile bool g_burst_mode = true;
volatile uint32_t g_single_width_us = 50;
volatile uint32_t g_gap_us = 2000;
volatile uint32_t g_frame_gap_us = 20000;
volatile uint32_t g_slope_half_period_us = 5000;

static void pulse_pin(gpio_num_t pin, uint32_t width_us) {
  gpio_set_level(pin, 1);
  delayMicroseconds(width_us);
  gpio_set_level(pin, 0);
}

// Let the scheduler run during multi-millisecond waits while keeping the
// final short tail in a busy wait for pulse timing.
static void cooperative_delay_us(uint32_t duration_us) {
  if (duration_us == 0) {
    return;
  }

  int64_t deadline_us = esp_timer_get_time() + static_cast<int64_t>(duration_us);
  for (;;) {
    int64_t remaining_us = deadline_us - esp_timer_get_time();
    if (remaining_us <= 0) {
      return;
    }

    TickType_t sleep_ticks = pdMS_TO_TICKS(static_cast<uint32_t>((remaining_us - 1000) / 1000));
    if (remaining_us > 2000 && sleep_ticks > 0) {
      vTaskDelay(sleep_ticks);
      continue;
    }

    delayMicroseconds(static_cast<uint32_t>(remaining_us));
    return;
  }
}

static void configure_slope_output(uint32_t half_period_us) {
  uint32_t frequency_hz = static_cast<uint32_t>(500000ULL / max<uint32_t>(half_period_us, 1));
  if (frequency_hz == 0) {
    frequency_hz = 1;
  }

  ledcSetup(CH2_SLOPE_PWM_CHANNEL, frequency_hz, CH2_SLOPE_PWM_BITS);
  ledcAttachPin(PIN_CH2_SLOPE, CH2_SLOPE_PWM_CHANNEL);
  ledcWrite(CH2_SLOPE_PWM_CHANNEL, CH2_SLOPE_PWM_DUTY);
}

static void print_status() {
  Serial.println();
  Serial.println("OWON ESP32 trigger jig");
  Serial.print("mode: ");
  Serial.println(g_burst_mode ? "burst" : "single");
  Serial.print("single_width_us: ");
  Serial.println(g_single_width_us);
  Serial.print("gap_us: ");
  Serial.println(g_gap_us);
  Serial.print("frame_gap_us: ");
  Serial.println(g_frame_gap_us);
  Serial.print("slope_half_period_us: ");
  Serial.println(g_slope_half_period_us);
  Serial.println("commands:");
  Serial.println("  burst");
  Serial.println("  single <width_us>");
  Serial.println("  gap <us>");
  Serial.println("  frame <us>");
  Serial.println("  half <us>");
  Serial.println("  status");
  Serial.println();
}

static void handle_command(const String &line) {
  String command = line;
  command.trim();
  if (command.length() == 0) {
    return;
  }

  if (command.equalsIgnoreCase("burst")) {
    g_burst_mode = true;
    print_status();
    return;
  }

  if (command.equalsIgnoreCase("status")) {
    print_status();
    return;
  }

  int split = command.indexOf(' ');
  String key = split < 0 ? command : command.substring(0, split);
  String value = split < 0 ? "" : command.substring(split + 1);
  value.trim();

  if (key.equalsIgnoreCase("single")) {
    uint32_t width = value.toInt();
    if (width > 0) {
      g_burst_mode = false;
      g_single_width_us = width;
      print_status();
    }
    return;
  }

  if (key.equalsIgnoreCase("gap")) {
    uint32_t us = value.toInt();
    if (us > 0) {
      g_gap_us = us;
      print_status();
    }
    return;
  }

  if (key.equalsIgnoreCase("frame")) {
    uint32_t us = value.toInt();
    if (us > 0) {
      g_frame_gap_us = us;
      print_status();
    }
    return;
  }

  if (key.equalsIgnoreCase("half")) {
    uint32_t us = value.toInt();
    if (us > 0) {
      g_slope_half_period_us = us;
      configure_slope_output(g_slope_half_period_us);
      print_status();
    }
    return;
  }

  Serial.print("unknown command: ");
  Serial.println(command);
}

static void serial_task(void *arg) {
  (void)arg;
  String line;
  for (;;) {
    while (Serial.available() > 0) {
      char c = static_cast<char>(Serial.read());
      if (c == '\n' || c == '\r') {
        if (line.length() > 0) {
          handle_command(line);
          line = "";
        }
      } else {
        line += c;
      }
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

static void pulse_task(void *arg) {
  (void)arg;
  for (;;) {
    pulse_pin(PIN_CH3_MARKER, 5);

    if (g_burst_mode) {
      for (size_t i = 0; i < sizeof(BURST_WIDTHS_US) / sizeof(BURST_WIDTHS_US[0]); ++i) {
        pulse_pin(PIN_CH1_DIRECT, BURST_WIDTHS_US[i]);
        cooperative_delay_us(g_gap_us);
      }
    } else {
      pulse_pin(PIN_CH1_DIRECT, g_single_width_us);
    }

    cooperative_delay_us(g_frame_gap_us);
  }
}

void setup() {
  Serial.begin(115200);
  delay(200);

  pinMode(PIN_CH1_DIRECT, OUTPUT);
  pinMode(PIN_CH2_SLOPE, OUTPUT);
  pinMode(PIN_CH3_MARKER, OUTPUT);

  gpio_set_level(PIN_CH1_DIRECT, 0);
  gpio_set_level(PIN_CH2_SLOPE, 0);
  gpio_set_level(PIN_CH3_MARKER, 0);
  configure_slope_output(g_slope_half_period_us);

  print_status();

  xTaskCreatePinnedToCore(serial_task, "serial_task", 4096, nullptr, 1, nullptr, 0);
  xTaskCreatePinnedToCore(pulse_task, "pulse_task", 4096, nullptr, 2, nullptr, 0);
}

void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
}
