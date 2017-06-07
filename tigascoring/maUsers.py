from __future__ import division
from datetime import datetime, timedelta

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc  # latex resources
from operator import itemgetter
from math import log
from sklearn.preprocessing import minmax_scale

import ma

_cat2exp = np.array([[1, 1, 2, 2], [2, 2, 3, 3], [3, 3, 4, 4]]) - 1


class Dsmmry(dict):
    def __init__(self, xLast=25, n=5, v=0.00005):

        self.adultRprts = np.zeros(7, dtype='int')
        self.bSiteRprts = np.zeros(7, dtype='int')
        self.missionRprts = 0
        self.flaggedRprts = 0

        self.smmryTime = 0
        self.k = 4
        self.n = n
        self.v = v
        self.xLast = xLast

    def smmry0_get(self):
        self.adultRprts = np.zeros(7)
        self.bSiteRprts = np.zeros(7)
        self.missionRprts = 0
        self.flaggedRprts = 0
        for uSmmry in self.values():
            self.adultRprts += uSmmry.adultRprts
            self.bSiteRprts += uSmmry.bSiteRprts
            self.missionRprts += uSmmry.missionRprts
            self.flaggedRprts += uSmmry.flaggedRprts

    def smmry0(self):
        self.smmry0_get()
        print '-' * 68
        print '+++ Users:   %6.0i' % len(self)
        print '+++ Rprts:   %6.0i' % (
            np.sum(self.adultRprts) + np.sum(self.bSiteRprts) + self.missionRprts + self.flaggedRprts),
        print ' ' * 16, 'summary time ... %s' % self.smmryTime
        print '-' * 68
        print '               ttl.    NC     hd     -2     -1      0     +1     +2'
        print '+++  adults:', '%6.0i' % np.sum(self.adultRprts),
        for n in self.adultRprts: print '%6.0i' % int(n),
        print
        print '+++  bSites:', '%6.0i' % np.sum(self.bSiteRprts),
        for n in self.bSiteRprts: print '%6.0i' % int(n),
        print
        print '+++ mission:', '%6.0i' % np.sum(self.missionRprts)
        print '+++ flagged:', '%6.0i' % np.sum(self.flaggedRprts)
        print '-' * 68

    def smmry1_get(self):
        nCounts = np.zeros(2)
        for uSmmry in self.values():
            uCounts = uSmmry.adultRprts[0] + np.sum(uSmmry.adultRprts[2:])
            uCounts += uSmmry.bSiteRprts[0] + np.sum(uSmmry.bSiteRprts[2:])
            nCounts[uCounts > self.n] += 1
        return nCounts

    def smmry1(self):
        nCounts = self.smmry1_get()
        print '+++    Usrs  #Rprts<=n  #Rprts>n'
        print '     %6.0i      %5.0i     %5.0i' % (len(self), nCounts[0], nCounts[1])
        print '                %6.2f     %5.2f' % (nCounts[0] / len(self), nCounts[1] / len(self))
        print

    def smmry2(self):

        nCounts = np.zeros(33).reshape(3, 11)

        for uSmmry in self.values():
            binNumber = (10 if np.sum(uSmmry.adultRprts) >= 10 else np.sum(uSmmry.adultRprts))
            nCounts[0, binNumber] += 1
            binNumber = (10 if np.sum(uSmmry.bSiteRprts) >= 10 else np.sum(uSmmry.bSiteRprts))
            nCounts[1, binNumber] += 1
            binNumber = (10 if uSmmry.missionRprts >= 10 else uSmmry.missionRprts)
            nCounts[2, binNumber] += 1

        axs = plt.subplot()
        axs.set_xticks(np.array(range(11)) * 3 + 1)
        axs.set_xticklabels(range(11))
        axs.bar(range(33), nCounts.T.flatten(), color=['y', 'm', 'c'])
        plt.show()

    def smmry3_get(self):
        nCounts = np.zeros(2)
        for uSmmry in self.values():
            nCounts[uSmmry.movIdx() > self.v] += 1
        return nCounts

    def smmry3(self):
        nCounts = self.smmry3_get()
        print '+++    Usrs movIdx<=v   movIdx>v'
        print '     %6.0i    %5.0i      %5.0i' % (len(self), nCounts[0], nCounts[1])
        print '              %6.2f      %5.2f' % (nCounts[0] / len(self), nCounts[1] / len(self))
        print

    def movIdx_plot(self, movMax=100):
        movIdx = [min(uSmmry.movIdx(), movMax) for uSmmry in self.values()]
        plt.plot(movIdx)
        plt.show()

    # +++ bayesian Network methods

    # empirical counts
    def counts_get(self):

        # reprtType/ExpClss join counts
        self.nRpEx = np.zeros(2 * self.k).reshape(2, self.k)
        # adultRprt/ExpClss join counts
        self.nAdEx = np.zeros(7 * self.k).reshape(7, self.k)
        # bSiteRprt/ExpClss join counts
        self.nBsEx = np.zeros(7 * self.k).reshape(7, self.k)

        # expertise-category prior counts
        cCounts = np.zeros(28).reshape(7, 4)

        for uSmmry in self.values():
            cCounts[:, uSmmry.nvIdx(n=self.n, v=self.v)] += uSmmry.adultRprts + uSmmry.bSiteRprts
            eCounts = uSmmry.expCounts(uSmmry.adultRprts, n=self.n, v=self.v)
            self.nRpEx[0,] += np.sum(eCounts, axis=0)
            self.nAdEx += eCounts
            eCounts = uSmmry.expCounts(uSmmry.bSiteRprts, n=self.n, v=self.v)
            self.nRpEx[1,] += np.sum(eCounts, axis=0)
            self.nBsEx += eCounts

        # expertise-category prior
        # do not count not-classified reports
        self.nExCat = np.array([np.sum(cCounts[1:4, ], axis=0), cCounts[4,], np.sum(cCounts[5:, ], axis=0)])

        # expertise-class prior
        # do not count not-classified reports
        self.nExCls = np.sum(self.nAdEx[1:, ], axis=0) + np.sum(self.nBsEx[1:, ], axis=0)

    # empirical (join)conditional distributions
    def distro_get(self):

        # laplacian smoothing
        self.nExCat += 1
        self.nExCls += 1
        self.nRpEx += 1
        self.nAdEx += 1
        self.nBsEx += 1

        # expertise-category prior
        self.nExCat /= np.sum(self.nExCat)

        # expertise-class prior
        self.nExCls /= np.sum(self.nExCls)

        # redistribute not classified reports proportionally
        w = np.sum(self.nAdEx[1:, ], axis=0) / np.sum(self.nAdEx[1:, ])
        self.nAdEx[0,] = w * np.sum(self.nAdEx[0,])
        w = np.sum(self.nBsEx[1:, ], axis=0) / np.sum(self.nBsEx[1:, ])
        self.nBsEx[0,] = w * np.sum(self.nBsEx[0,])

        # A. join distribution
        if self.p == 1:
            self.nRpEx /= np.sum(self.nRpEx)
            self.nAdEx /= np.sum(self.nAdEx)
            self.nBsEx /= np.sum(self.nBsEx)

        # B. conditional distributions
        elif self.p == 2:
            for k in range(self.k):
                self.nRpEx[:, k] /= np.sum(self.nRpEx[:, k])
                self.nAdEx[:, k] /= np.sum(self.nAdEx[:, k])
                self.nBsEx[:, k] /= np.sum(self.nBsEx[:, k])

    # heading line
    def headLine(self, label):
        print
        print '+++   %s   ' % label,
        for k in range(self.k): print '    %1.0i  ' % (k + 1),
        print
        print '-' * 46

    # check self.counts_get() is done
    def counts_chk(self):
        if not hasattr(self, 'nExCls'):
            self.counts_get()
            if self.p: self.distro_get()

    # expertise-category prior distribution
    def catPrior(self):
        self.counts_chk()
        print
        print '+++           #R<=n&mI<=v  #R<=n&mI>v  #R>n&mI<=v   #R>n&mI>v'
        print '-' * 62
        if self.p == 0:
            for k in range(self.nExCat.shape[0]):
                print '+++   cat.=%1i     %5.0i       %5.0i        %5.0i       %5.0i  ' % (
                    (k + 1,) + tuple(self.nExCat[k,]))
        else:
            for k in range(self.nExCat.shape[0]):
                print '+++   cat.=%1i      %6.4f      %6.4f      %6.4f      %6.4f  ' % (
                    (k + 1,) + tuple(self.nExCat[k,]))
        print
        nExCls = np.zeros(4)
        for cRow, eRow in zip(self.nExCat, _cat2exp):
            for c, e in zip(cRow, eRow): nExCls[e] += c
        self.headLine('expCat')
        print ' ' * 14,
        for k in range(self.k):
            if self.p == 0:
                print ' %6.0i' % nExCls[k],
            else:
                print ' %6.4f' % nExCls[k],
        print

    # expertise-class prior distribution
    def expPrior(self):
        self.counts_chk()
        self.headLine('expCls')
        print ' ' * 14,
        if self.p == 0:
            for k in range(self.k):    print ' %6.0i' % self.nExCls[k],
        else:
            for k in range(self.k):    print ' %6.4f' % self.nExCls[k],
        print

    # reportType (join)conditional distribution
    def rTypeCond(self):
        self.counts_chk()
        self.headLine('Rprts.')
        for row, label in zip(self.nRpEx, [' adult ', ' bSite ']):
            print '+++  %s  ' % label,
            if self.p == 0:
                for k in range(self.k):    print ' %6.0i' % row[k],
            else:
                for k in range(self.k):    print ' %6.4f' % row[k],
            print
        print '-' * 46
        print ' ' * 14,
        for row in self.nRpEx.T:
            if self.p == 0:
                print ' %6.0i' % np.sum(row),
            else:
                print ' %6.4f' % np.sum(row),
        print

    # adultRprts/bSiteRprts (join)conditional distributions
    def rClssCond(self):
        self.counts_chk()
        for nCounts, label in zip([self.nAdEx, self.nBsEx], ['adultR', 'bSiteR']):
            self.headLine(label)
            for row, label in zip(nCounts, ['--', 'hd', '-2', '-1', ' 0', '+1', '+2']):
                print '+++     %s    ' % label,
                if self.p == 0:
                    for k in range(self.k):    print ' %6.0i' % row[k],
                else:
                    for k in range(self.k):    print ' %6.4f' % row[k],
                print
            print '-' * 46
            print ' ' * 14,
            for row in nCounts.T:
                if self.p == 0:
                    print ' %6.0i' % np.sum(row),
                else:
                    print ' %6.4f' % np.sum(row),
            print

    # compute bayesian network distributions
    def bayesNet(self, p=0):
        # get bayesNet parameters
        self.p = p
        self.counts_get()
        if self.p: self.distro_get()
        # expertise-category prior distribution
        self.catPrior()
        # expertise-class prior distribution
        self.expPrior()
        # reportType (join)conditional distribution
        self.rTypeCond()
        # adultRprts/bSiteRprts classification (join)conditional distributions
        self.rClssCond()

    # +++ expertise-class conditional distributions

    def expCond_get(self):

        # get bayesNet parameters
        self.p = 2
        self.counts_get()
        self.distro_get()

        # expertise to adultR conditional distribution
        self.nExAd = self.nAdEx * self.nRpEx[0,] * self.nExCls
        self.nExAd = self.nExAd.T / np.sum(self.nExAd, axis=1)

        # expertise to bSiteR conditional distribution
        self.nExBs = self.nBsEx * self.nRpEx[1,] * self.nExCls
        self.nExBs = self.nExBs.T / np.sum(self.nExBs, axis=1)

        # column binding
        self.nExAB = np.hstack((self.nExAd, self.nExBs))

    def expCond(self):

        self.expCond_get()

        # heading line
        def headLine(label):
            print
            print '+++  %s  ' % label,
            for l in ['--', 'hd', '-2', '-1', ' 0', '+1', '+2']: print '  %s   ' % l,
            print
            print '-' * 68

        # expertise-class join(cond) distributions
        for nCounts, label in zip([self.nExAd, self.nExBs], ['adultR', 'bSiteR']):
            # feature heading line
            headLine(label)
            for row, c in zip(nCounts, range(self.k)):
                print '+++  expC=%s ' % (c + 1),
                for k in range(self.nExAd.shape[1]):
                    print ' %6.4f' % row[k],
                print
            print '-' * 68
            print

    # +++ score-rank computation methods

    def getScore(self, uuid):
        score = 1
        if uuid in self.keys():
            score = int(self.rank.index(uuid) / len(self.rank) * 90) + 1
        if score > 66:
            label = "user_score_pro"
        elif 33 < score <= 66:
            label = "user_score_advanced"
        else:
            label = "user_score_beginner"
        return (score, label)

    def uScore(self, uSmmry):
        S = np.log(np.ones(self.k) / self.k)
        for c in uSmmry.xLastRprts:
            S += np.log(self.nExAB[:, c])
            S -= np.max(S)
            S -= np.log(np.sum(np.exp(S)))
        S += np.log(np.linspace(0.25, 1, 4))
        S -= np.max(S)
        S -= np.log(np.sum(np.exp(S)))
        return -np.sum(S)

    def uScoring(self):
        for uSmmry in self.values():
            uSmmry.score = self.uScore(uSmmry)

    def rank_get(self):
        self.expCond_get()
        self.uScoring()
        sRank = sorted([(uuid, uSmmry.score, uSmmry.movIdx()) for uuid, uSmmry in self.items()], key=itemgetter(1, 2))
        self.rank = [uRank[0] for uRank in sRank]

    # +++ score-rank visualization methods

    def rank_tbl(self):
        if not hasattr(self, 'rank'): self.rank_get()
        score, counts, n, Counts = -1, 0, 0, -1
        for uuid in self.rank:
            if self[uuid].score != score:
                score = self[uuid].score  # expertise-class distribution
                counts = 0
                n += 1
                print
            counts += 1
            Counts += 1
            print '%6i ... %14.8f, ... %6i %8i ' % (n, score, counts, Counts), self[uuid].xLastRprts, '\r',

    def rank_shw(self):
        if not hasattr(self, 'rank'): self.rank_get()
        for uuid in self.rank: self[uuid].showIt()

    def rank_plt(self, ylim=(0.0, 1.1)):

        if not hasattr(self, 'rank'): self.rank_get()

        X = np.array([rank_uData(self[uuid]) for uuid in self.rank])

        plt.ylim(ylim)
        plt.grid(True)
        # movIdx
        plt.plot(minmax_scale(X[:, 1]), color='y', label='movIdx')
        # number of bSite reports
        plt.plot(minmax_scale(X[:, 3]), color='c', label='bSites')
        # number of adult reports
        plt.plot(minmax_scale(X[:, 2]), color='m', label='adults')
        # score
        plt.plot(minmax_scale(X[:, 0]), color='b', label='uScore')
        # legend
        plt.legend(loc='upper left')
        plt.title('+++ scaled logscore +++')
        plt.show()


class Usmmry:
    def __init__(self, uuid):

        self.uuid = uuid
        self.adultRprts = np.zeros(7, dtype='int')
        self.bSiteRprts = np.zeros(7, dtype='int')
        self.xLastRprts = []
        self.missionRprts = 0
        self.flaggedRprts = 0
        self.coordList = []
        self.score = None

    def addCoord(self, Coords):
        if all([coord != None for coord in Coords]) and all(
                [coord != 0.0 for coord in Coords]) and Coords not in self.coordList:
            self.coordList.append(Coords)

    def ttlRprts(self):
        return np.sum(self.adultRprts) + np.sum(self.bSiteRprts) + self.missionRprts

    def movIdx(self):
        if len(self.coordList) > 1:
            z = np.array([[complex(lon, lat) for lon, lat in self.coordList]])
            return np.sum(abs(z.T - z) ** 2) / (2 * z.shape[1] ** 2)
        else:
            return 0

    def nvIdx(self, n=2, v=0):
        # take into account only not hidden reports
        adultR = self.adultRprts[0] + np.sum(self.adultRprts[2:])
        bSiteR = self.bSiteRprts[0] + np.sum(self.bSiteRprts[2:])
        i = int((adultR + bSiteR) > n)
        j = int(self.movIdx() > v)
        return int(str(i) + str(j), 2)

    def expCounts(self, uCounts, n=2, v=0):
        eCounts = np.zeros(28).reshape(7, 4)
        nv = self.nvIdx(n=n, v=v)
        eCounts[0, nv] = uCounts[0]
        eCounts[1, _cat2exp[0, nv]] = uCounts[1]
        eCounts[2, _cat2exp[0, nv]] = uCounts[2]
        eCounts[3, _cat2exp[0, nv]] = uCounts[3]
        eCounts[4, _cat2exp[1, nv]] = uCounts[4]
        eCounts[5, _cat2exp[2, nv]] = uCounts[5]
        eCounts[6, _cat2exp[2, nv]] = uCounts[6]
        return eCounts

    def showIt(self):
        print
        print '+++ userId.', self.uuid
        print 'adultR.', np.sum(self.adultRprts), '...', self.adultRprts
        print 'bSiteR.', np.sum(self.bSiteRprts), '...', self.bSiteRprts
        print 'mission', self.missionRprts
        print 'flggedR', self.flaggedRprts
        print 'Coords.', self.coordList
        print 'movIdx.', self.movIdx()
        print 'uScore.', self.score

    def detail(self):
        with ma.connect() as dbConn:
            with ma.Cursor(dbConn) as crsr:
                sql = """SELECT A.type, A.mission_id, A.location_choice,  A.current_location_lon, A.current_location_lat, A.selected_location_lon, A.selected_location_lat, A.hide,  A.point, B.report_id, B.user_id, B.tiger_certainty_category FROM tigaserver_app_report as A RIGHT JOIN tigacrafting_expertreportannotation AS B ON A."version_UUID" = B.report_id WHERE (A.user_id = (%s) AND B.validation_complete = TRUE) ORDER by A.server_upload_time; """
                crsr.execute(sql, (self.uuid,))
                crsr.browse()


def smmry(xLast=20, n=10, v=0.0002, fromyear=2015, toyear=3000, ret=True):
    with ma.connect() as dbConn:
        with ma.Cursor(dbConn) as crsr:

            # Att!! I'm currently not taking into account hiden reports neither B.status={1:'public', 0:'flagged', -1:'hidden'} to score
            if fromyear == None:
                sql = """SELECT A.user_id, A.hide, A.type, A.location_choice, A.current_location_lon, A.current_location_lat, A.selected_location_lon, A.selected_location_lat, B.status, B.tiger_certainty_category, B.site_certainty_category FROM tigaserver_app_report AS A RIGHT JOIN tigacrafting_expertreportannotation AS B ON A."version_UUID" = B.report_id ORDER by A.server_upload_time; """
                crsr.execute(sql)
            else:
                sql = """SELECT A.user_id, A.type, A.hide, A.location_choice, A.current_location_lon, A.current_location_lat, A.selected_location_lon, A.selected_location_lat, B.status, B.tiger_certainty_category, B.site_certainty_category FROM tigaserver_app_report as A RIGHT JOIN tigacrafting_expertreportannotation AS B ON A."version_UUID" = B.report_id WHERE (extract(year from A.server_upload_time) >= (%s) AND extract(year from A.server_upload_time) < (%s)) ORDER by A.server_upload_time; """
                crsr.execute(sql, (fromyear, toyear))

            startTime = datetime.now()
            dSmmry = Dsmmry(xLast=xLast, n=n, v=v)
            while crsr.rownumber < crsr.rowcount:
                iRow = crsr.rowInstance()
                uuid = iRow['user_id']

                # check/add user summary
                if uuid not in dSmmry.keys():
                    dSmmry[uuid] = Usmmry(uuid)

                # ignore flagged reports (status == 0)
                if iRow['status'] == 0:
                    dSmmry[uuid].flaggedRprts += 1
                    continue

                # update reports counts
                if iRow['type'] == 'adult':

                    if iRow['hide'] or iRow['status'] == -1:
                        idxRprt = 1
                    else:
                        if iRow['tiger_certainty_category'] == None:
                            idxRprt = 0
                        else:
                            idxRprt = iRow['tiger_certainty_category'] + 4

                    dSmmry[uuid].adultRprts[idxRprt] += 1
                    dSmmry[uuid].xLastRprts.append(idxRprt)

                elif iRow['type'] == 'site':

                    if iRow['hide'] or iRow['status'] == -1:
                        idxRprt = 1
                    else:
                        if iRow['site_certainty_category'] == None:
                            idxRprt = 0
                        else:
                            idxRprt = iRow['site_certainty_category'] + 4

                    dSmmry[uuid].bSiteRprts[idxRprt] += 1
                    dSmmry[uuid].xLastRprts.append(idxRprt + 7)

                elif iRow['type'] == 'mission':
                    dSmmry[uuid].missionRprts += 1

                # update user_report_coordinates list
                if iRow['type'] != 'mission':
                    # do not take into account hidden reports here
                    if not iRow['hide'] and iRow['status'] == 1:
                        if iRow['location_choice'] == 'current':
                            dSmmry[uuid].addCoord((iRow['current_location_lon'], iRow['current_location_lat']))
                        elif iRow['location_choice'] == 'selected':
                            dSmmry[uuid].addCoord((iRow['selected_location_lon'], iRow['selected_location_lat']))

                # check xLastRprts length is not greater than x
                if len(dSmmry[uuid].xLastRprts) > dSmmry.xLast:
                    dSmmry[uuid].xLastRprts.pop()

            dSmmry.smmryTime = datetime.now() - startTime
            dSmmry.smmry0()
            dSmmry.rank_get()

    if ret: return dSmmry


# +++ smmry comparison functions +++


def rank_uData(uSmmry):
    uScore = uSmmry.score if uSmmry.score != None else 0
    uMvIdx = uSmmry.movIdx()
    uMvIdx = log(uMvIdx, 10) if uMvIdx > 1 else 0
    uAdult = np.sum(uSmmry.adultRprts)
    ubSite = np.sum(uSmmry.bSiteRprts)

    return np.array([uScore, uMvIdx, uAdult, ubSite])


def rank_comp(sList, theta=1, lList=None):
    if lList == None:
        lList = []
        for s in sList:
            if theta == 1:
                lList.append(r'$\theta_1=\,%s,\,\theta_2=\,%6.2e$' % (str(s.n).zfill(2), s.v))
            elif theta == 3:
                lList.append(r'$\theta_3=\,%2.0i$' % s.xLast)

    plt.grid(True)

    for s, l, c in zip(sList, lList, ['b', 'r', 'g']):
        X = np.array([rank_uData(s[uuid]) for uuid in s.rank])
        # score
        plt.plot(X[:, 0], color=c, label=l)

    # legend
    plt.legend(loc='upper left')
    plt.title('+++ logscore +++')
    plt.show()
