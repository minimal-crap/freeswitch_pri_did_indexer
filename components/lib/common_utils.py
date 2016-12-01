import time
import datetime


class Queue:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0, item)

    def dequeue(self):
        return self.items.pop()

    def size(self):
        return len(self.items)


class CommonMethods:
    def __init__(self):
        pass

    epoch_pattern = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def datetime_to_epoch(datetime_obj):
        try:
            if type(datetime_obj) != datetime.datetime:
                raise Exception("Invalid input type, datetime object expected!")
            return int(
                time.mktime(
                    time.strptime(
                        str(datetime_obj).split(".")[0],
                        CommonMethods.epoch_pattern
                    )
                )
            )

        except Exception as err:
            print err

    @staticmethod
    def epoch_to_datetime(epoch):
        try:
            if type(epoch) != int:
                raise Exception("Invalid input type, int epoch value expected!")

            return time.strftime(
                CommonMethods.epoch_pattern,
                time.localtime(epoch)
            )
        except Exception as err:
            print err



