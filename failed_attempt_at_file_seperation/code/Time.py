def time_to_date(time): # Time is in hours.
    year = 0
    month = 0
    day = 0
    year = int(time // 8760)
    if(year > 0):
        time = time - year * 8760
    month = int(time // 720)
    if(month > 0):
        time = time - month * 720
    day = int(time // 24)
    if(day > 0):
        time = time - day * 24
    return number_to_day(day) + "." + number_to_month(month) + "." + number_to_year(year)

def number_to_year(num):
    if(num > 999):
        return str(num)
    elif(num > 99):
        return "0"+str(num)
    elif(num > 9):
        return "00"+str(num)
    return "000"+str(num)

def number_to_month(num):
    if(num > 9):
        return str(num)
    return "0"+str(num)

def number_to_day(num):
    if(num > 9):
        return str(num)
    return "0"+str(num)