def is_old(inst):
	if inst.version in (17, 18):
		return True


def set_old(inst):
	inst.version = 17


def get_game(inst):
	if is_old(inst):
		return 'Old'
	return 'Unknown Game'


games = ['Old', 'Unknown Game']


