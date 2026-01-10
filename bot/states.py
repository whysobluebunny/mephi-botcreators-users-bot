from aiogram.fsm.state import State, StatesGroup


class UploadState(StatesGroup):
    waiting_files = State()
