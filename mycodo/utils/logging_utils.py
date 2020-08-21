# coding=utf-8

def set_log_level(logging_):
    if logging_.getLevelName(logging_.getLogger().getEffectiveLevel()) == 'CRITICAL':
        return logging_.CRITICAL
    elif logging_.getLevelName(logging_.getLogger().getEffectiveLevel()) == 'ERROR':
        return logging_.ERROR
    elif logging_.getLevelName(logging_.getLogger().getEffectiveLevel()) == 'WARNING':
        return logging_.WARNING
    elif logging_.getLevelName(logging_.getLogger().getEffectiveLevel()) == 'INFO':
        return logging_.INFO
    elif logging_.getLevelName(logging_.getLogger().getEffectiveLevel()) == 'DEBUG':
        return logging_.DEBUG
