def fnv1a_32(string, seed=0):
	"""
	Returns: The FNV-1a (alternate) hash of a given string
	"""
	#Constants
	FNV_prime = 16777619
	offset_basis = 2166136261

	#FNV-1a Hash Function
	hash = offset_basis + seed
	for char in string:
		hash = hash ^ ord(char)
		hash = hash * FNV_prime
	return hash