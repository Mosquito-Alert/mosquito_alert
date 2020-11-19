from __future__ import division
from datetime import datetime, date, timedelta

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc  # latex resources
from operator import itemgetter, attrgetter
from math import log
from sklearn.preprocessing import minmax_scale

import tigascoring.ma as ma

# using 4 prior expertise-categories
_catK = 4
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# using 4 prior expertise_classes
# _clsK = 4
# _cat2exp = np.array([[1, 1, 1, 1], [1, 1, 2, 2], [2, 3, 3, 4], [3, 4, 4, 4]]) -1
# using 5 prior expertise_classes
# _clsK = 5
# _cat2exp = np.array([[1, 1, 1, 1], [2, 3, 3, 3], [4, 3, 3, 3], [4, 5, 5, 5]]) -1
# using 6 prior expertise_classes
_clsK = 6
_cat2exp = np.array([[1, 1, 1, 2], [2, 2, 3, 3], [3, 4, 4, 4], [5, 6, 6, 6]]) - 1

# list of super-experts (super_bcn, super_movelab, super_reritja)
_expertIds = [23, 24, 25]


# +++ AT.!!!
# 1. for rprts with masterLbl == None and no consensus in expertLbl (this should not occur) we use the average label from expertLbl;
# 2. if at least one expert decides to hide the report we take this decision as mandatory, independently of what the others say;
# 3. in case 2 we still take into account the location to compute the user's mobility index.

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Class: Report Summary
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class Report:
    def __init__(self, reportId, iRow):

        self.id = reportId
        self.date = iRow['server_upload_time']
        self.type = iRow['type']
        self.location = (None, None)
        self.masterLbl = None
        self.expertLbl = []

        self.setLocation(iRow)

    def setLocation(self, iRow):
        if not iRow['hide']:
            location = (None, None)
            if iRow['location_choice'] == 'current':
                location = (iRow['current_location_lon'], iRow['current_location_lat'])
            elif iRow['location_choice'] == 'selected':
                location = (iRow['selected_location_lon'], iRow['selected_location_lat'])
            if all([lonlat != None for lonlat in location]) and all([lonlat != 0.0 for lonlat in location]):
                self.location = location

    def iRowLbl(self, iRow):
        rprtLbl = None
        if (iRow['status'] == -1 or iRow['hide']):
            rprtLbl = 1
        else:
            if iRow['type'] == 'adult':
                if iRow['tiger_certainty_category'] == None:
                    rprtLbl = 0
                else:
                    rprtLbl = iRow['tiger_certainty_category'] + 4
            elif iRow['type'] == 'site':
                if iRow['site_certainty_category'] == None:
                    rprtLbl = 0
                else:
                    rprtLbl = iRow['site_certainty_category'] + 4
        return rprtLbl

    def addLbl(self, iRow):
        rprtLbl = self.iRowLbl(iRow)
        if iRow['expert_id'] in _expertIds:
            self.masterLbl = rprtLbl
        else:
            if rprtLbl != 0:
                self.expertLbl.append(self.iRowLbl(iRow))

    def getLbl(self):

        rprtLbl = 0
        if self.masterLbl != None and self.masterLbl != 0:
            # Att !!!
            # the master can either not say anything (there is no record with a master id in the validation table) or say nothing (there is a record in the validation table with validation == None)
            rprtLbl = self.masterLbl
        else:
            if 1 in self.expertLbl:
                # Att !!!
                # at least one expert has decided to hide the report !!,
                # in this case we take this decision as mandatory
                rprtLbl = 1
            elif len(self.expertLbl):
                rprtLbl = int(round(sum(self.expertLbl) / len(self.expertLbl), 0))

        if self.type == 'site':
            siteReLbl = [0, 1, 2, 2, 3, 4, 4]
            rprtLbl = siteReLbl[rprtLbl]

        return rprtLbl

    def showIt(self):
        print
        print ('+++++ ID: %s' % self.id)
        print ('    date: %s' % self.date)
        print ('    type: %s' % self.type)
        print ('location: %9.5r, %9.5r' % self.location)
        print ('   label:', self.getLbl(), ':', self.masterLbl, '.', self.expertLbl)


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Class: User Summary
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class Usmmry:
    def __init__(self, uuid):

        self.uuid = uuid
        self.rprtDict = {}
        self.score = None

    def flaggedRprts(self):
        return len([rprt for rprt in self.rprtDict.values() if rprt.getLbl() == -2])

    def rprtList(self, rType):
        if rType == 'adult':
            rList = np.zeros(7, dtype='int')
        elif rType == 'site':
            rList = np.zeros(5, dtype='int')
        for rprt in self.rprtDict.values():
            if rprt.type == rType: rList[rprt.getLbl()] += 1
        return rList

    def sortDict(self):
        # Att. !!!
        # filter out not-classified reports to avoid the non-monotonic scoring problem
        classifiedR = [rprt for rprt in self.rprtDict.values() if rprt.getLbl()]
        return sorted(classifiedR, key=attrgetter('date'))

    def xLastR(self, rType, xLast):
        sortDict = self.sortDict()
        if rType == 'adult':
            rList = np.zeros(7, dtype='int')
        elif rType == 'site':
            rList = np.zeros(5, dtype='int')
        for rprt in sortDict[-xLast:]:
            if rprt.type == rType: rList[rprt.getLbl()] += 1
        return rList

    def locList(self):
        return [rprt.location for rprt in self.rprtDict.values()]

    def movIdx(self):
        locList = self.locList()
        if len(locList) > 1:
            z = np.array([[complex(lon, lat) for lon, lat in locList if (lon != None and lat != None)]])
            return np.sum(abs(z.T - z) ** 2) / (2 * z.shape[1] ** 2)
        else:
            return 0

    def logMI(self):
        MI = self.movIdx()
        if MI > 1:
            logMI = log(MI, 10)
        else:
            logMI = 0
        return logMI

    def nvIdx(self, n, v):
        adultR = self.rprtList('adult')
        bSiteR = self.rprtList('site')
        # take into account only not hidden reports
        i = int((np.sum(adultR) - adultR[1] + np.sum(bSiteR) - bSiteR[1]) > n)
        j = int(self.movIdx() > v)
        return int(str(i) + str(j), 2)

    def showIt(self):
        print
        print ('+++ userId.', self.uuid)
        print ('    adultR.', np.sum(self.rprtList('adult')), '...', self.rprtList('adult'))
        print ('    bSiteR.', np.sum(self.rprtList('site')), '...', self.rprtList('site'))
        print ('  location.', self.locList())
        print ('    movIdx.', self.movIdx())
        print ('    uScore.', self.score)

    def chkIt(self):
        self.showIt()
        for rprt in self.rprtDict.values(): rprt.showIt()

    def detail(self):
        with ma.connect() as dbConn:
            with ma.Cursor(dbConn) as crsr:
                sql = """SELECT A.hide, A.type, A.mission_id, A.location_choice,  A.current_location_lon, A.current_location_lat, A.selected_location_lon, A.selected_location_lat, B.report_id, B.user_id as expert_id, B.status, B.tiger_certainty_category, B.site_certainty_category FROM tigaserver_app_report as A RIGHT JOIN tigacrafting_expertreportannotation AS B ON A."version_UUID" = B.report_id WHERE (A.user_id = (%s) AND B.validation_complete = TRUE) ORDER by A.server_upload_time; """
                crsr.execute(sql, (self.uuid,))
                crsr.browse()


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Class: Global Summary
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class Dsmmry(dict):
    def __init__(self, n, v, xLast):

        self.adultRprts = np.zeros(7, dtype='int')
        self.bSiteRprts = np.zeros(5, dtype='int')
        self.flaggedRprts = 0

        self.smmryTime = 0
        self.k = _clsK
        self.n = n
        self.v = v
        self.xLast = xLast
        self.p = 0

    def smmry0_get(self):
        self.adultRprts = np.zeros(7)
        self.bSiteRprts = np.zeros(5)
        self.flaggedRprts = 0
        for uSmmry in self.values():
            self.adultRprts += uSmmry.rprtList('adult')
            self.bSiteRprts += uSmmry.rprtList('site')
            self.flaggedRprts += uSmmry.flaggedRprts()

    def smmry0(self):
        self.smmry0_get()
        nvIdx = np.array([uSmmry.nvIdx(self.n, self.v) for uSmmry in self.values()])
        nv0 = np.where(nvIdx == 0)[0].shape[0]
        nv1 = np.where(nvIdx == 1)[0].shape[0]
        nv2 = np.where(nvIdx == 2)[0].shape[0]
        nv3 = np.where(nvIdx == 3)[0].shape[0]
        print ('-' * 68)
        print ('+++   Users: %6i' % len(self))
        print ('+++   Rprts: %6i' % (np.sum(self.adultRprts) + np.sum(self.bSiteRprts) + self.flaggedRprts)),
        if np.sum(self.flaggedRprts):
            print ('(flagged: %6.0i)' % np.sum(self.flaggedRprts)),
        print
        print ('-' * 68)
        print (' ' * 26, '          movIdx<=v             movIdx>v ')
        print (' ' * 26, ' %13.0i(%.2f)  %13.0i(%.2f)' % (
        (nv0 + nv2), (nv0 + nv2) / len(nvIdx), (nv1 + nv3), (nv1 + nv3) / len(nvIdx)))
        print ('+++   #R<=n:  %5i(%.2f)   %13.f(%.2f)  %13.f(%.2f) ' % (
        (nv0 + nv1), (nv0 + nv1) / len(nvIdx), nv0, nv0 / len(nvIdx), nv1, nv1 / len(nvIdx)))
        print ('+++    #R>n:  %5i(%.2f)   %13.f(%.2f)  %13.f(%.2f) ' % (
        (nv2 + nv3), (nv2 + nv3) / len(nvIdx), nv2, nv2 / len(nvIdx), nv3, nv3 / len(nvIdx)))
        print ('-' * 68)
        print ('               ttl.     NC     hd     -2     -1      0     +1     +2')
        print ('+++  adults:', '%6.0i' % np.sum(self.adultRprts)),
        for n in self.adultRprts: print ('%6.0i' % int(n)),
        print
        print (' ' * 19,)
        for n in self.adultRprts: print ('  %.2f' % (n / np.sum(self.adultRprts))),
        print
        print ('-' * 68)
        print ('               ttl.     NC     hd     -1      0     +1')
        print ('+++  bSites:', '%6.0i' % np.sum(self.bSiteRprts)),
        for n in self.bSiteRprts: print ('%6.0i' % int(n)),
        print
        print (' ' * 19),
        for n in self.bSiteRprts: print ('  %.2f' % (n / np.sum(self.bSiteRprts))),
        print
        print ('-' * 68)
        print (' ' * 36, 'summary time ... %s' % self.smmryTime)

    def smmry2_old(self):

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

    def usrRprt_hst(self, maxRprt=100):
        repx = [min(uSmmry.ttlRprts(), maxRprt) for uSmmry in self.values()]
        plt.hist(repx, bins=maxRprt, color='r')
        plt.xlabel("#Reports")
        plt.ylabel("#Users")
        plt.show()

    def movIdx_hst(self, perc=90):
        movIdx = [uSmmry.movIdx() for uSmmry in self.values()]
        maxMI = np.percentile(movIdx, perc)
        movIdx = [min(MI, maxMI) for MI in movIdx]
        plt.hist(movIdx, bins=perc + 1, color='b')
        plt.xlabel("movIndex")
        plt.ylabel("#Users")
        plt.show()

    # +++ bayesian Network methods

    def adCounts(self, uCounts, nv):
        eCounts = np.zeros(7 * self.k).reshape(7, self.k)
        eCounts[0, nv] = uCounts[0]
        eCounts[1, _cat2exp[0, nv]] = uCounts[1]
        eCounts[2, _cat2exp[1, nv]] = uCounts[2]
        eCounts[3, _cat2exp[1, nv]] = uCounts[3]
        eCounts[4, _cat2exp[2, nv]] = uCounts[4]
        eCounts[5, _cat2exp[3, nv]] = uCounts[5]
        eCounts[6, _cat2exp[3, nv]] = uCounts[6]
        return eCounts

    def bSCounts(self, uCounts, nv):
        eCounts = np.zeros(5 * self.k).reshape(5, self.k)
        eCounts[0, nv] = uCounts[0]
        eCounts[1, _cat2exp[0, nv]] = uCounts[1]
        eCounts[2, _cat2exp[1, nv]] = uCounts[2]
        eCounts[3, _cat2exp[2, nv]] = uCounts[3]
        eCounts[4, _cat2exp[3, nv]] = uCounts[4]
        return eCounts

    # empirical counts
    def counts_get(self):

        # reprtType/ExpClss join counts
        self.nRpEx = np.zeros(2 * self.k).reshape(2, self.k)
        # adultRprt/ExpClss join counts
        self.nAdEx = np.zeros(7 * self.k).reshape(7, self.k)
        # bSiteRprt/ExpClss join counts
        self.nBsEx = np.zeros(5 * self.k).reshape(5, self.k)

        # expertise-category prior
        self.nExCat = np.zeros(_catK * 4).reshape(_catK, 4)

        for uSmmry in self.values():
            nv = uSmmry.nvIdx(n=self.n, v=self.v)

            # counting by expertise categories
            # do NOT count not-classified reports here
            adultR = uSmmry.rprtList('adult')
            self.nExCat[:, nv] += np.array([adultR[1], np.sum(adultR[2:4]), adultR[4], np.sum(adultR[5:])])
            bSiteR = uSmmry.rprtList('site')
            self.nExCat[:, nv] += bSiteR[1:]

            # counting by expertise classes

            # do count not-classified reports here
            eCounts = self.adCounts(adultR, nv)
            self.nRpEx[0,] += np.sum(eCounts, axis=0)
            self.nAdEx += eCounts
            eCounts = self.bSCounts(bSiteR, nv)
            self.nRpEx[1,] += np.sum(eCounts, axis=0)
            self.nBsEx += eCounts

        # # do NOT count not-classified reports here
        # # !! Att. see file chkScore1.txt
        # eCounts = self.adCounts(adultR, nv)
        # self.nRpEx[0, ] += np.sum(eCounts[1:, ], axis=0)
        # self.nAdEx[1:, ] += eCounts[1:, ]
        # eCounts = self.bSCounts(bSiteR, nv)
        # self.nRpEx[1, ] += np.sum(eCounts[1:, ], axis=0)
        # self.nBsEx[1:, ] += eCounts[1:, ]

        # expertise-class prior
        # do NOT count not-classified reports here
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
        # !!! Att.
        # results in an equal weight of None-type through expertise-classes
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

    # output exCls distribution line
    def shwLine(self, headLbl=None, rowLbl=None, nExCls=None):
        if headLbl is not None:
            print
            print ('+++  %s ' % headLbl),
            for k in range(self.k): print ('    %1.0i  ' % (k + 1)),
            print
            print ('-' * 60)
        if nExCls is not None:
            if rowLbl is not None:
                print ('%s' % rowLbl.center(11, ' ')),
            else:
                print (' ' * 11),
            if self.p == 0:
                for k in range(self.k):    print (' %6.0i' % nExCls[k]),
            else:
                for k in range(self.k):    print (' %6.4f' % nExCls[k]),
            print

    # check self.counts_get() is done
    def counts_chk(self):
        if not hasattr(self, 'nExCls'):
            self.counts_get()
            if self.p: self.distro_get()

    # expertise-category prior distribution
    def catPrior(self):
        self.counts_chk()
        print
        print ('+++           #R<=n&mI<=v  #R<=n&mI>v  #R>n&mI<=v  #R>n&mI>v')
        print ('-' * 60)
        if self.p == 0:
            for k in range(self.nExCat.shape[0]):
                print ('+++    cat%1i     %6.0i      %6.0i       %6.0i      %6.0i  ' % (
                (k + 1,) + tuple(self.nExCat[k,])))
        else:
            for k in range(self.nExCat.shape[0]):
                print ('+++    cat%1i      %6.4f      %6.4f      %6.4f      %6.4f  ' % (
                (k + 1,) + tuple(self.nExCat[k,])))
        print
        # to check equality with expertise-class prior (self.nExCls)
        nExCls = np.zeros(self.k)
        for cRow, eRow in zip(self.nExCat, _cat2exp):
            for c, e in zip(cRow, eRow): nExCls[e] += c
        self.shwLine(headLbl='expCat', nExCls=nExCls)

    # expertise-class prior distribution
    def expPrior(self):
        self.counts_chk()
        self.shwLine(headLbl='expCls', nExCls=self.nExCls)

    # reportType (join)conditional distribution
    def rTypeCond(self):
        self.counts_chk()
        self.shwLine(headLbl='Rprts.')
        for row, label in zip(self.nRpEx, [' adult ', ' bSite ']):
            self.shwLine(rowLbl=label, nExCls=row)
        print ('-' * 60)
        self.shwLine(nExCls=np.sum(self.nRpEx.T, axis=1))

    # adultRprts/bSiteRprts (join)conditional distributions
    def rClssCond(self):
        self.counts_chk()
        # +++ adultReports
        self.shwLine(headLbl='adultR')
        for row, rLabel in zip(self.nAdEx, ['--', 'hd', '-2', '-1', ' 0', '+1', '+2']):
            self.shwLine(rowLbl=rLabel, nExCls=row)
        print ('-' * 60)
        self.shwLine(nExCls=np.sum(self.nAdEx.T, axis=1))
        # +++ bSiteReports
        self.shwLine(headLbl='bSiteR')
        for row, rLabel in zip(self.nBsEx, ['--', 'hd', '-1', ' 0', '+1']):
            self.shwLine(rowLbl=rLabel, nExCls=row)
        print ('-' * 60)
        self.shwLine(nExCls=np.sum(self.nBsEx.T, axis=1))

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

    def expCond(self):
        self.expCond_get()
        # +++ adultReports
        print
        print ('+++  %s  ' % 'adultR',)
        for l in ['--', 'hd', '-2', '-1', ' 0', '+1', '+2']: print ('  %s   ' % l,)
        print
        print ('-' * 68)
        for row, c in zip(self.nExAd, range(self.k)):
            print ('+++  expC=%s ' % (c + 1),)
            for k in range(self.nExAd.shape[1]):
                print (' %6.4f' % row[k],)
            print
        print ('-' * 68)
        print
        # +++ bSiteReports
        print
        print ('+++  %s  ' % 'bSiteR',)
        for l in ['--', 'hd', '-1', ' 0', '+1']: print ('  %s   ' % l,)
        print
        print ('-' * 52)
        for row, c in zip(self.nExBs, range(self.k)):
            print ('+++  expC=%s ' % (c + 1),)
            for k in range(self.nExBs.shape[1]):
                print (' %6.4f' % row[k],)
            print
        print ('-' * 52)
        print

    # +++ score-rank computation methods

    def uScore(self, uSmmry):
        S = np.log(np.ones(self.k) / self.k)
        # use xLast reports only to score
        for rprt in uSmmry.sortDict()[-self.xLast:]:
            if rprt.type == 'adult':
                S += np.log(self.nExAd[:, rprt.getLbl()])
            elif rprt.type == 'site':
                S += np.log(self.nExBs[:, rprt.getLbl()])
        S -= np.log(np.sum(np.exp(S)))
        S += np.log(np.linspace(1.0 / self.k, 1, self.k))
        return np.sum(np.exp(S))

    def rank_get(self, xLast=None):
        self.expCond_get()
        if xLast != None: self.xLast = xLast
        for uSmmry in self.values(): uSmmry.score = self.uScore(uSmmry)
        sRank = sorted([(uuid, uSmmry.score, uSmmry.movIdx()) for uuid, uSmmry in self.items()], key=itemgetter(1, 2))
        self.rank = [uRank[0] for uRank in sRank]

    def getScore(self, uuid):
        score = 1
        if uuid in self.keys():
            score = int(self.rank.index(uuid) / len(self.rank) * 93) + 2
        if score > 66:
            label = "user_score_pro"
        elif 33 < score <= 66:
            label = "user_score_advanced"
        else:
            label = "user_score_beginner"
        return (score, label)

    # +++ score-rank visualization methods

    def rank_tbl(self):
        if not hasattr(self, 'rank'): self.rank_get()
        fSmmry = Usmmry('tmp')
        score, counts, n, Counts = -1, 0, 0, -1
        for uuid in self.rank:
            if self[uuid].score != score:
                score = self[uuid].score  # expertise-class distribution
                counts = 0
                n += 1
                print
            counts += 1
            Counts += 1
            print ('%6i ... %14.8f, ... %6i %8i ' % (n, score, counts, Counts),)
            # show xLast reports used to score
            print (self[uuid].xLastR('adult', self.xLast),)
            print (self[uuid].xLastR('site', self.xLast), '\r',)

    def rank_plt(self, ylim=(0.0, 1.1)):
        if not hasattr(self, 'rank'): self.rank_get()
        fig, axs = plt.subplots(figsize=(13, 5))
        axs.set_ylim(ylim)
        axs.grid(True)
        # movIdx
        X = np.array([self[uuid].logMI() for uuid in self.rank])
        axs.plot(minmax_scale(X), color='y', label='movIdx')
        # number of bSite reports
        X = np.array([np.sum(self[uuid].xLastR('site', self.xLast)) for uuid in self.rank], dtype='float')
        axs.plot(minmax_scale(X), color='c', label='bSites')
        # number of adult reports
        X = np.array([np.sum(self[uuid].xLastR('adult', self.xLast)) for uuid in self.rank], dtype='float')
        axs.plot(minmax_scale(X), color='m', label='adults')
        # score
        X = np.array([self[uuid].score for uuid in self.rank])
        axs.plot(X, color='b', label='uScore')
        # legend
        plt.legend(loc='upper left')
        # plt.title('+++ ranked scoring +++')
        plt.show()


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Function: Get Global Summry
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def smmry(n=2, v=1e-08, fromYear=2015, toDate='31-12-2999', shw=True, ret=True, xLast=20):
    with ma.connect() as dbConn:
        with ma.Cursor(dbConn) as crsr:

            # Att!! I'm currently not taking into account hiden reports neither B.status={1:'public', 0:'flagged', -1:'hidden'} to score
            if fromYear == None:
                sql = """SELECT A.user_id, A.hide, A.type, A.server_upload_time, A.location_choice, A.current_location_lon, A.current_location_lat, A.selected_location_lon, A.selected_location_lat, B.report_id, B.user_id as expert_id, B.status, B.tiger_certainty_category, B.site_certainty_category FROM tigaserver_app_report AS A RIGHT JOIN tigacrafting_expertreportannotation AS B ON A."version_UUID" = B.report_id ORDER by A.server_upload_time DESC; """
                crsr.execute(sql)
            else:
                sql = """SELECT A.user_id, A.type, A.hide, A.server_upload_time, A.location_choice, A.current_location_lon, A.current_location_lat, A.selected_location_lon, A.selected_location_lat, B.report_id, B.user_id as expert_id, B.status, B.tiger_certainty_category, B.site_certainty_category FROM tigaserver_app_report as A RIGHT JOIN tigacrafting_expertreportannotation AS B ON A."version_UUID" = B.report_id WHERE (extract(year from A.server_upload_time) >= (%s) AND A.server_upload_time <= (%s)) ORDER by A.server_upload_time DESC; """
                crsr.execute(sql, (fromYear, toDate))

            startTime = datetime.now()
            dSmmry = Dsmmry(n=n, v=v, xLast=xLast)

            while crsr.rownumber < crsr.rowcount:

                iRow = crsr.rowInstance()

                # ignore flagged reports (status == 0) and/or mission reports
                if iRow['status'] == 0 or iRow['type'] == 'mission':
                    continue

                uuid = iRow['user_id']
                rprtId = iRow['report_id']

                # check/add user in dSmmry
                if uuid not in dSmmry.keys():
                    dSmmry[uuid] = Usmmry(uuid)

                # check/add report in uSmmry
                if rprtId not in dSmmry[uuid].rprtDict.keys():
                    dSmmry[uuid].rprtDict[rprtId] = Report(rprtId, iRow)
                # add report label
                dSmmry[uuid].rprtDict[rprtId].addLbl(iRow)

            if shw:
                dSmmry.smmryTime = datetime.now() - startTime
                dSmmry.smmry0()
                dSmmry.catPrior()
                dSmmry.expCond()

            dSmmry.rank_get()

    if ret: return dSmmry
