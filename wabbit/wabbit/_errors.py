"""All Wabbit language compiler errors."""


class WabbitError(Exception):
    pass


class WabbitSyntaxError(WabbitError):
    pass
