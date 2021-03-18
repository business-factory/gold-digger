from gunicorn import glogging

from ..di import DiContainer


class GunicornLogger(glogging.Logger):
    """
    Custom logger for Gunicorn log messages.
    """

    def setup(self, cfg):
        """
        :type cfg: gunicorn.config.Config
        """
        # this is also executed when importing whole gold_digger package
        DiContainer.set_up_root_logger()

        # disables StreamHandler
        # https://github.com/benoitc/gunicorn/blob/master/gunicorn/glogging.py#L400
        cfg.set("accesslog", None)
        cfg.set("errorlog", None)

        super().setup(cfg)
        self.error_log.propagate = True
        self.access_log.propagate = True
