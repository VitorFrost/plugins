# -*- coding: utf-8 -*-
# filename: ~/.pioreactor/plugins/sense_ph.py

import click

from pioreactor.whoami import get_unit_name, get_latest_experiment_name
from pioreactor.config import config
from pioreactor.background_jobs.base import BackgroundJob
from pioreactor.utils import local_persistant_storage
from pioreactor.utils.timing import RepeatedTimer
from pioreactor.hardware import SCL, SDA

from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_ads1x15.ads1115 import ADS1115 as ADS
from busio import I2C

__plugin_summary__ = (
    "enter desc here"
)
__plugin_version__ = "0.0.1"
__plugin_name__ = "pH_Sensor"
__plugin_author__ = "Cam DP"

class PHSensor(BackgroundJob):

    published_settings = {
        "pH": {"datatype": "float", "settable": False},
    }

    def __init__(self, sample_rate, unit, experiment):
        super().__init__(job_name="sense_ph", unit=unit, experiment=experiment)
        self.ads = ADS(I2C(SCL, SDA), data_rate=128, gain=1)
        self.analog_in = AnalogIn(self.ads, 0)
        self.pH = None

        self.read_ph_timer = RepeatedTimer(
            interval=1/sample_rate, # convert to seconds
            function=self.read_ph,
            run_immediately=True,
        ).start()

    def read_ph(self):
        raw = self.analog_in.voltage

        with local_persistant_storage("ph_calibration") as cache:
            # this published to MQTT
            self.pH = raw # raw_to_calibrated(raw, cache) #raw_to_calibrated to be defined...

    def on_ready_to_sleeping(self) -> None:
        self.read_ph_timer.pause()

    def on_sleeping_to_ready(self) -> None:
        self.read_ph_timer.unpause()

    def on_disconnect(self) -> None:
        self.read_ph_timer.cancel()


@click.command(name="sense_ph")
def click_sense_ph():
    """
    Start the pH sensor
    """

    job = PHSensor(
        sample_rate=1,
        unit=get_unit_name(),
        experiment=get_latest_experiment_name(),
    )
    job.block_until_disconnected()

