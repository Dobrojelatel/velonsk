# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date

def format_timedelta(p_delta, p_time):
    def format_something(p_count, p_names):
        if p_count == 1:
            return str(1) + " " + p_names[0]
        elif p_count <=4:
            return str(p_count) + " " + p_names[1]
        elif p_count <= 20:
            return str(p_count)  + " " + p_names[2]
        else:
            cnt2 = p_count % 10
            if cnt2 == 0:
                return str(p_count)  + " " + p_names[2]
            elif cnt2 == 1:
                return str(1) + " " + p_names[0]
            elif cnt2 <=4:
                return str(p_count) + " " + p_names[1]
            else:
                return str(p_count)  + " " + p_names[2]
            
    suf = " назад"
    rez = ""
#    if p_delta.days/365 >= 1:
#        rez = format_something(p_delta.days/365,["год","года","лет"]) + suf
#    elif p_delta.days/30 >= 1:
#        rez = format_something(p_delta.days/30,["месяц","месяца","месяцев"]) + suf
#    elif p_delta.days/7 >= 1:
#        rez = format_something(p_delta.days/7,["неделю","недели","недель"]) + suf
#    elif p_delta.days >= 1:
#        rez = format_something(p_delta.days,["день","дня","дней"]) + suf
#    elif p_delta.seconds/3600 >= 1:
#        rez = format_something(p_delta.seconds/3600,["час","часа","часов"]) + suf
    today = (datetime.now() + timedelta(hours=7)).date()
    yesterday = today - timedelta(days=1)
    if p_time.date()< yesterday:
        rez = p_time.strftime("%d.%m.%y %H:%M")
    elif p_time.date()< today:
        rez = "вчера в " + p_time.strftime("%H:%M")
    elif p_delta.seconds/3600 >= 1:
        rez = "сегодня в " + p_time.strftime("%H:%M")
    elif p_delta.seconds/60 >= 1:
        rez = format_something(p_delta.seconds/60,["минуту","минуты","минут"]) + suf
    else:
        rez = "Только что"
    return rez.decode("utf-8")
