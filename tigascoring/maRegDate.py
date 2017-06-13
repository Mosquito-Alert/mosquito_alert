import matplotlib.pyplot as plt

import ma
import matplotlib.pyplot as plt

import ma


def usrRegDate():
    dbConn = ma.connect()
    tUsers = ma.Table(dbConn, 'tUsers')
    tUsers.selectAll()

    regDate = {}
    for user in tUsers.cursor.fetchall():
        yearMonth = '%d%s' % (user[1].year, str(user[1].month).zfill(2))
        if yearMonth not in regDate: regDate[yearMonth] = 0
        regDate[yearMonth] += 1

    ma.disconnect(dbConn)

    keyList = regDate.keys()
    keyList.sort()

    colorLst = ['y', 'm', 'c', 'r', 'g', 'b']
    yearLst = list(set([date[:4] for date in keyList]))
    yearLst.sort()
    yearCol = [colorLst[yearLst.index(date[:4])] for date in keyList]

    axs = plt.subplot()
    axs.set_xticks(range(len(regDate)))
    axs.set_xticklabels([key[-2:] for key in keyList])
    axs.bar(range(len(regDate)), [regDate[key] for key in keyList], color=yearCol)
    plt.show()

    return
