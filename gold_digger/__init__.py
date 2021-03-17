from .di import DiContainer as _DiContainer


def di_container(main_file_path):
    return _DiContainer(main_file_path)


_DiContainer.set_up_root_logger()
