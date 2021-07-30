'''create insurance plan id'''
import string

def plan_id(dictionary:dict, location:str, client:str) -> None:
    '''create a plan id using address, name, and plan'''
    pland_id = [
        dictionary["PayorName"],
        dictionary["PlanName"],
        dictionary["AddressPayor"],
        dictionary["CityPayor"],
        dictionary["StatePayor"],
        dictionary["ZipPayor"][:5],
        location
    ]
    pland_id = "".join("".join(pland_id).split()).upper()
    hashed = []
    for ascii_idx in pland_id:
        try:
            hashed.append((string.ascii_uppercase.index(ascii_idx) + 1))
        except ValueError:
            try:
                hashed.append((int(ascii_idx) + 1))
            except ValueError:
                pass
    hash_id = 1
    for num in hashed:
        hash_id = hash_id * num
    hash_id = str(hash_id)[:8]
    dictionary["PlanID"] = client + hash_id
