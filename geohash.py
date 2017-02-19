#!/usr/sbin/env python
#fileencoding=utf-8
'''
@author: huangjin (Jeff)
@email: hj51yc@gmail.com
'''

import sys

def bin(s):
    return str(s) if s<=1 else bin(s>>1) + str(s&1)
        
class GeoHash(object):
    
    def __init__(self, HASH_LENGTH=8):
        self._HASH_LENGTH = int(HASH_LENGTH)
        self._ENCODE_TB = ['0', '1', '2', '3', '4', '5', '6', '7', '8',  '9', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'm', 'n', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z' ]
        self._DECODE_TB = {}
        for i in xrange(len(self._ENCODE_TB)):
            self._DECODE_TB[self._ENCODE_TB[i]] = i
        self._TOTAL_BITS_LEN = self._HASH_LENGTH * 5
        ## latitude bit length
        self._YBITS_LEN = self._TOTAL_BITS_LEN / 2
        ## longitude bit length
        self._XBITS_LEN = self._YBITS_LEN
        if self._TOTAL_BITS_LEN % 2 == 1:
            self._XBITS_LEN += 1

        ## longitude and latitude min block length
        xblocks = 1 << self._XBITS_LEN
        self._X_MIN_BLOCK_LEN = 360.0 / float(xblocks)
        yblocks = 1 << self._YBITS_LEN
        self._Y_MIN_BLOCK_LEN = 180.0 / float(yblocks)



    def _find_bits(self, low, high, cur, bit_len):
        if low >= high:
            print "low value is bigger than high!!"
            exit(1)
        bits = []
        low = float(low)
        high = float(high)
        for i in xrange(bit_len):
            mid = (low + high)/2
            if cur < mid:
                bits.append('0')
                high = mid
            else:
                bits.append('1')
                low = mid
        return bits
            
    def _find_value(self, low, high, bits):
        if low >= high:
            print "low value is bigger than high!!"
            exit(1)
        low = float(low)
        high = float(high)
        for i in xrange(0,len(bits)):
            mid = (low + high) / 2
            if bits[i] == '0':
                high = mid
            else:
                low = mid
        return (low, high)
    
    def _encode_base32(self, merger_bits):
        if len(merger_bits) != self._TOTAL_BITS_LEN:
            print "fatal: _encode_base32(self, merger_bits) => bits length should be %d "%self._TOTAL_BITS_LEN
            exit(1)
        encode_chrs = []
        for i in xrange(self._HASH_LENGTH):
            five_bits = merger_bits[i*5:(i+1)*5]
            bits_str = ''.join(five_bits)
            ch = self._ENCODE_TB[int(bits_str,2)]
            encode_chrs.append(ch)
        return ''.join(encode_chrs)


    def encode(self, longitude, latitude):
        if longitude < -180 or longitude > 180:
            print 'longitude must between in [-180, 180]'
            exit(1)
        if latitude < -90 or latitude > 90:
            print 'latitude must between in [-90, 90]'
            exit(2)
        xbits_len = self._XBITS_LEN
        ybits_len = self._YBITS_LEN
        xbits = self._find_bits(-180, 180, longitude, xbits_len)
        ybits = self._find_bits(-90, 90, latitude, ybits_len)
        merger_bits = []
        for i in xrange(ybits_len):
            merger_bits.append(xbits[i])
            merger_bits.append(ybits[i])
        if ybits_len < xbits_len:
            merger_bits.append(xbits[ybits_len])
        print merger_bits
        return self._encode_base32(merger_bits)
    
    
    def decode(self,encode_str):
        merger_bits = []
        for ch in encode_str:
            if ch not in self._DECODE_TB:
                print 'encoded str:"%s" not legal'%encode_str
                exit(1)
            n = self._DECODE_TB[ch]
            bin_str = bin(n)
            len_bits = len(bin_str)
            ## fill 0 when bin_str's length less than 5
            for i in xrange(5 - len_bits):
                merger_bits.append('0')
            for i in xrange(len(bin_str)):
                merger_bits.append(bin_str[i])
        xbits = []
        ybits = []
        i = 0
        print merger_bits
        K = len(merger_bits)
        while i < K:
            xbits.append(merger_bits[i])
            i += 2
        i = 1
        while i < K:
            ybits.append(merger_bits[i])
            i += 2
        (x_low, x_high) = self._find_value(-180, 180, xbits)
        (y_low, y_high) = self._find_value(-90, 90, ybits)
        return [(x_low, x_high), (y_low, y_high)]

    
    def _find_bound_bits(self, low, high, min_block_len, blow, bhigh):
        low = float(low)
        high = float(high)
        thresh = float(min_block_len) / 2
        blow = float(blow)
        bhigh = float(bhigh)
        if high - low < min_block_len or bhigh - blow < min_block_len:
            print "high - low must bigger than %"%min_block_len
            exit(1)
        if blow < low or bhigh > high:
            print "[blow,bhigh] not in [low, high]!"
            exit(2)

        que = {(low, high, blow, bhigh):''}
        res_codes = []
        c = 0
        while True:
            if len(que) == 0:
                break
            cur_block = (high - low) / (1 << c)
            if cur_block <= min_block_len:
                for (l, h, bl, bh) in que:
                    res_codes.append(que[(l, h, bl, bh)])
                break
            new_que = {}
            for (l, h, bl, bh) in que:
                codes = que[(l, h, bl, bh)]
                mid = (l + h) / 2
                ## full included in left or right block, just put them in the result
                if bh == mid and bl == l:
                    res_codes.append(codes + '0')
                elif bl == mid and bh == h:
                    res_codes.append(codes + '1')
                elif bh <= mid:
                    if bh - bl > thresh:
                        new_que[(l, mid, bl, bh)] = codes + '0'
                    else:
                        pass
                elif bl >= mid:
                    if bh - bl > thresh:
                        new_que[(mid, h, bl, bh)] = codes + '1'
                    else:
                        pass
                else:
                    ## partial included then put them in the queue
                    flag = False
                    if mid - bl > thresh:
                        new_que[(l, mid, bl, mid)] = codes + '0'
                    if bh - mid > thresh:
                        new_que[(mid, h, mid, bh)] = codes + '1'
            que = new_que
            c += 1
        return res_codes
    

    def _all_possible_bits(self, bits_len):
        bits_len = int(bits_len)
        if bits_len <= 0:
            print "fatal: _all_possible_bits(bits_len), the bits_len should bigger than 0"
        que = ['']
        for i in xrange(bits_len):
            new_que = []
            for s in que:
                new_que.append(s + '0')
                new_que.append(s + '1')
            que = new_que
        return que

    def _fill_bits_codes(self, codes_list, bits_len):
        final_codes = []
        for bits_code in codes_list:
            cur_len = len(bits_code)
            leave_len = bits_len - cur_len
            if leave_len == 0:
                final_codes.append(bits_code)
                continue
            if leave_len < 0:
                print 'fatal: int _fill_bits_codes() bits_len is short than some code in codes_list!!'
                exit(1)
            all_bits_str = self._all_possible_bits(leave_len)
            for s in all_bits_str:
                final_codes.append(bits_code + s)
        return final_codes


    ## find related code combination
    ## x is longitude , y is latitude
    def bound_codes(self, x_low, x_high, y_low, y_high):
        xbits_tmp_list = self._find_bound_bits(-180.0, 180.0, self._X_MIN_BLOCK_LEN, x_low, x_high)
        ybits_tmp_list = self._find_bound_bits(-90.0, 90.0, self._Y_MIN_BLOCK_LEN, y_low, y_high)
        print 'xbits_tmp_list',xbits_tmp_list
        print 'ybits_tmp_list',ybits_tmp_list
        xbits_list = self._fill_bits_codes(xbits_tmp_list, self._XBITS_LEN)    
        ybits_list = self._fill_bits_codes(ybits_tmp_list, self._YBITS_LEN)
        print 'xbits_list',xbits_list
        print 'ybits_list',ybits_list
        

        codes_list = []
        for xbits in xbits_list:
            for ybits in ybits_list:
                merger_bits = []
                for i in xrange(self._YBITS_LEN):
                    merger_bits.append(xbits[i])
                    merger_bits.append(ybits[i])
                if self._YBITS_LEN < self._XBITS_LEN:
                    merger_bits.append(xbits[self._XBITS_LEN - 1])
                base32_str = self._encode_base32(merger_bits)
                codes_list.append(base32_str)
        return codes_list

        

if __name__ == "__main__":
    geohash = GeoHash(8)
    loc = (116.3906,39.92324)
    print 'org loc:',loc
    s = geohash.encode(loc[0],loc[1])
    print 'encode:',s
    b = geohash.decode(s)
    print 'decode:',b

    geohash = GeoHash(4)
    codes_list = geohash.bound_codes(0,3,-0.5,0.5)
    print codes_list
            
