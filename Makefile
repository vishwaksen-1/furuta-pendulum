# Furuta Pendulum (Raspberry Pi Pico / MicroPython)
#
# Usage (as requested):
#   make test            # flash+reset all tests in order
#   make test 1          # flash+reset only test #1
#   make test 4          # flash+reset only test #4
#
#   make main linear     # flash+reset firmware/main-lin.py as :main.py
#   make main nl 1       # flash+reset firmware/main-nl-p.py as :main.py
#   make main nl 2       # flash+reset firmware/main-nl-full.py as :main.py

SHELL := /bin/sh

VENV ?= $(HOME)/vishwaksen/atp/dummy/venv
MPREMOTE ?= $(if $(wildcard $(VENV)/bin/mpremote),$(VENV)/bin/mpremote,mpremote)

MPREMOTE_CMD := $(MPREMOTE)

# Ordered test suite (matches firmware/README.md)
TEST_1 := firmware/test_i2c_scan.py
TEST_2 := firmware/test_encoder.py
TEST_3 := firmware/test_stepper.py
TEST_4 := firmware/test_velocity.py
TEST_5 := firmware/test_motor_encoder.py
TEST_6 := firmware/test_step_rate.py

TEST_NUMS_ALL := 1 2 3 4 5 6
TEST_NUMS_SEL := $(filter $(TEST_NUMS_ALL),$(MAKECMDGOALS))

ifeq ($(strip $(TEST_NUMS_SEL)),)
TEST_FILES := $(foreach n,$(TEST_NUMS_ALL),$(TEST_$(n)))
else
TEST_FILES := $(foreach n,$(TEST_NUMS_SEL),$(TEST_$(n)))
endif

MAIN_FILE :=
ifneq ($(filter linear,$(MAKECMDGOALS)),)
MAIN_FILE := firmware/main-lin.py
else ifneq ($(filter nl,$(MAKECMDGOALS)),)
ifneq ($(filter 1,$(MAKECMDGOALS)),)
MAIN_FILE := firmware/main-nl-p.py
else ifneq ($(filter 2,$(MAKECMDGOALS)),)
MAIN_FILE := firmware/main-nl-full.py
endif
endif

.PHONY: help test main linear nl 1 2 3 4 5 6

help:
	@printf '%s\n' \
		'Targets:' \
		'  make test                       Flash+reset all tests in order' \
		'  make test 1                     Flash+reset test #1 as :main.py' \
		'  make test 2                     Flash+reset test #2 as :main.py' \
		'  ...                             (up to test #6)' \
		'  make main linear                Flash+reset firmware/main-lin.py as :main.py' \
		'  make main nl 1                  Flash+reset firmware/main-nl-p.py as :main.py' \
		'  make main nl 2                  Flash+reset firmware/main-nl-full.py as :main.py' \
		'' \
		'Variables (override like: make VENV=~/path/to/venv):' \
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
	if [ -z "$(MAIN_FILE)" ]; then \
		printf '%s\n' "Usage:"; \
		printf '%s\n' "  make main linear"; \
		printf '%s\n' "  make main nl 1"; \
		printf '%s\n' "  make main nl 2"; \
		exit 2; \
	fi; \
	printf '%s\n' "==> flashing $(MAIN_FILE) -> :main.py"; \
	$(MPREMOTE_CMD) fs cp "$(MAIN_FILE)" :main.py; \
	$(MPREMOTE_CMD) reset

# These targets exist only so `make test 1` / `make main nl 2` don't error.
linear nl 1 2 3 4 5 6:
	@:
