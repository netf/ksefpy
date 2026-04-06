from enum import StrEnum


class SchemaVersion(StrEnum):
    FA_2 = "FA(2)"
    FA_3 = "FA(3)"
    FA_PEF_3 = "FA_PEF(3)"
    FA_KOR_PEF_3 = "FA_KOR_PEF(3)"
    FA_RR = "FA_RR"
