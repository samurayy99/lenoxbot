from gmgn_wrapper.gmgn.client import gmgn

gmgn = gmgn()

getNewPairs = gmgn.getNewPairs(limit=1)

print(getNewPairs)