import numpy as np

from pymodaq_utils.utils import ThreadCommand
from pymodaq_data.data import DataToExport
from pymodaq_gui.parameter import Parameter

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins


from pymodaq_plugins_wika.hardware.wika import WikaController, get_devices_list


class DAQ_0DViewer_Wika(DAQ_Viewer_base):
    """ Wika plugin class for a OD viewer.
    Tested with Wika P-30 gauges.
    Runs on pmd 5 windows
    Needs to have installed the Wika drivers. 
    """
    controller_type = WikaController
    devices_COM, devices_serial = get_devices_list()

    params = comon_parameters+[
        {'title': 'Device list', 'name': 'device_list',
            'type': 'list', 'limits': devices_serial},
        {'title': 'Waiting time (s)', 'name': 'waiting_time',
            'type': 'float', 'value': 1},
        ]

    def ini_attributes(self):
        self.controller: self.controller_type = None
        self.serial_number = self.settings.child('device_list').value()
        self.waiting_time = self.settings.child('waiting_time').value()
        self.COM = self.devices_COM[self.serial_number]

    def commit_settings(self, param: Parameter):
        if param.name() == "waiting_time":
           self.waiting_time = param.value()

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        # raise NotImplementedError  # TODO when writing your own plugin remove this line and modify the one below
        if self.is_master:
            self.controller = self.controller_type()
            self.controller.open_communication(self.COM) # call eventual methods
            initialized = self.controller.online
            info = f"Initialized gauge {self.serial_number} on {self.COM}"
        else:
            self.controller = controller
            initialized = True

        self.dte_signal_temp.emit(DataToExport(name='Wika', data=[DataFromPlugins(name="pressure", data=np.array([0]),
                                                                dim='Data0D', labels=['Pressure'])]))


        return info, initialized

    def close(self):
        self.controller.close_communication()
        self.controller = None

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """

        data, _ = self.controller.grab_pressure(waiting_time = self.waiting_time)

        # synchrone version (blocking function)
        self.dte_signal.emit(DataToExport(name='Wika', data=[DataFromPlugins(name="pressure", data=data,
                                                                dim='Data0D', labels=['Pressure'])]))

    def stop(self):
        pass


if __name__ == '__main__':
    main(__file__)
