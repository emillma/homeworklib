class UsageChecker:
    password = PASSWORD
    usage = {}
    sneaky_reset = False

    @classmethod
    def reset_usage(cls, fkey, lock):
        if cls.password is not None and lock != cls.password:
            cls.sneaky_reset = True
        cls.usage[fkey] = 0

    @classmethod
    def increase_usage(cls, fkey):
        cls.usage[fkey] = cls.usage.get(fkey, 0) + 1

    @classmethod
    def get_usage(cls, fkey):
        return cls.usage[fkey]

    @classmethod
    def is_used(cls, fkey):
        if cls.sneaky_reset:
            print('sneaky_reset!')
            return False
        return cls.usage[fkey] != 0
