# Furuta Pendulum (Raspberry Pi Pico / MicroPython)
#
# Usage examples:
#   make test                    Flash+reset all tests in order
#   make test 1                  Flash+reset only test #1
#   make test 4                  Flash+reset only test #4
#
#   make main pd                 Flash+reset main.py with PD control
#   make main lqr                Flash+reset main.py with LQR control
#   make main nl-p               Flash+reset main.py with nonlinear P
#   make main nl-full            Flash+reset main.py with nonlinear full PD
#   make run-pd                  Flash main.py (PD) and run with mpremote
#
#   make clean                   Remove compiled cache

SHELL := /bin/sh

VENV ?= $(HOME)/vishwaksen/atp/dummy/venv
MPREMOTE ?= $(if $(wildcard $(VENV)/bin/mpremote),$(VENV)/bin/mpremote,mpremote)

MPREMOTE_CMD := $(MPREMOTE)

# Ordered test suite (in firmware/test/)
TEST_1 := firmware/test/test_i2c_scan.py
TEST_2 := firmware/test/test_encoder.py
TEST_3 := firmware/test/test_stepper.py
TEST_4 := firmware/test/test_velocity.py
TEST_5 := firmware/test/test_motor_encoder.py
TEST_6 := firmware/test/test_step_rate.py

TEST_NUMS_ALL := 1 2 3 4 5 6
TEST_NUMS_SEL := $(filter $(TEST_NUMS_ALL),$(MAKECMDGOALS))

ifeq ($(strip $(TEST_NUMS_SEL)),)
TEST_FILES := $(foreach n,$(TEST_NUMS_ALL),$(TEST_$(n)))
else
TEST_FILES := $(foreach n,$(TEST_NUMS_SEL),$(TEST_$(n)))
endif

# Main file selection based on strategy
MAIN_FILE := firmware/main.py
CONTROL_STRATEGY :=

ifneq ($(filter pd,$(MAKECMDGOALS)),)
CONTROL_STRATEGY := pd
else ifneq ($(filter lqr,$(MAKECMDGOALS)),)
CONTROL_STRATEGY := lqr
else ifneq ($(filter nl-p,$(MAKECMDGOALS)),)
CONTROL_STRATEGY := nl-p
else ifneq ($(filter nl-full,$(MAKECMDGOALS)),)
CONTROL_STRATEGY := nl-full
endif

.PHONY: help test main pd lqr nl-p nl-full run-pd run-lqr run-nl-p run-nl-full 1 2 3 4 5 6 clean

help:
	@printf '%s\n' \
		'Targets:' \
		'  make test                       Flash+reset all 6 tests in order' \
		'  make test 1..6                  Flash+reset specific test(s)' \
		'  make main pd                    Flash main.py with PD control strategy' \
		'  make main lqr                   Flash main.py with LQR control strategy' \
		'  make main nl-p                  Flash main.py with nonlinear P strategy' \
		'  make main nl-full               Flash main.py with nonlinear full PD strategy' \
		'  make run-pd                     Flash PD main and start interactive session' \
		'  make run-lqr                    Flash LQR main and start interactive session' \
		'  make run-nl-p                   Flash NL-P main and start interactive session' \
		'  make run-nl-full                Flash NL-Full main and start interactive session' \
		'  make clean                      Remove compiled files (__pycache__)' \
		'' \
		'Variables (override: make VENV=~/path/to/venv):' \
		'  VENV=$(HOME)/vishwaksen/atp/dummy/venv' \
		'  MPREMOTE=$(VENV)/bin/mpremote (auto-fallback to mpremote on PATH)'

test:
	@set -eu; \
	for f in $(TEST_FILES); do \
		printf '%s\n' "==> flashing $$f -> :main.py"; \
		$(MPREMOTE_CMD) fs cp "$$f" :main.py; \
		$(MPREMOTE_CMD) reset; \
	done

main:
	@set -eu; \
	if [ -z "$(CONTROL_STRATEGY)" ]; then \
		printf '%s\n' "Usage:"; \
		printf '%s\n' "  make main pd    (PD control)"; \
		printf '%s\n' "  make main lqr   (LQR control)"; \
		exit 2; \
	fi; \
	printf '%s\n' "==> flashing $(MAIN_FILE) -> :main.py (strategy: $(CONTROL_STRATEGY))"; \
	$(MPREMOTE_CMD) fs cp "$(MAIN_FILE)" :main.py; \
	$(MPREMOTE_CMD) fs cp "firmware/control_lib.py" :control_lib.py; \
	$(MPREMOTE_CMD) fs cp "firmware/control_strategies.py" :control_strategies.py; \
	$(MPREMOTE_CMD) reset

run-pd:
	@set -eu; \
	printf '%s\n' "==> flashing PD main and starting interactive session"; \
	$(MPREMOTE_CMD) fs cp "firmware/main.py" :main.py; \
	$(MPREMOTE_CMD) fs cp "firmware/control_lib.py" :control_lib.py; \
	$(MPREMOTE_CMD) fs cp "firmware/control_strategies.py" :control_strategies.py; \
	$(MPREMOTE_CMD) reset; \
	$(MPREMOTE_CMD)

run-lqr:
	@set -eu; \
	printf '%s\n' "==> flashing LQR main and starting interactive session"; \
	$(MPREMOTE_CMD) fs cp "firmware/main.py" :main.py; \
	$(MPREMOTE_CMD) fs cp "firmware/control_lib.py" :control_lib.py; \
	$(MPREMOTE_CMD) fs cp "firmware/control_strategies.py" :control_strategies.py; \
	$(MPREMOTE_CMD) reset; \
	$(MPREMOTE_CMD)

run-nl-p:
	@set -eu; \
	printf '%s\n' "==> flashing NL-P main and starting interactive session"; \
	$(MPREMOTE_CMD) fs cp "firmware/main.py" :main.py; \
	$(MPREMOTE_CMD) fs cp "firmware/control_lib.py" :control_lib.py; \
	$(MPREMOTE_CMD) fs cp "firmware/control_strategies.py" :control_strategies.py; \
	$(MPREMOTE_CMD) reset; \
	$(MPREMOTE_CMD)

run-nl-full:
	@set -eu; \
	printf '%s\n' "==> flashing NL-Full main and starting interactive session"; \
	$(MPREMOTE_CMD) fs cp "firmware/main.py" :main.py; \
	$(MPREMOTE_CMD) fs cp "firmware/control_lib.py" :control_lib.py; \
	$(MPREMOTE_CMD) fs cp "firmware/control_strategies.py" :control_strategies.py; \
	$(MPREMOTE_CMD) reset; \
	$(MPREMOTE_CMD)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete

# These targets exist so `make test 1` / `make main lqr` don't error.
pd lqr nl-p nl-full 1 2 3 4 5 6:
	@:
