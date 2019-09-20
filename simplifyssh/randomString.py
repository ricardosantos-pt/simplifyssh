import random
import string

def randomString(stringLength):
    """
        Generate a random string with the combination of lowercase and uppercase letters 
    """

    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(stringLength))