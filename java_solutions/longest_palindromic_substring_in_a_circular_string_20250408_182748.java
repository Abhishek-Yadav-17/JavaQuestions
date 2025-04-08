import java.util.Arrays;

class Solution {
    public String longestPalindromeCircular(String s) {
        if (s == null || s.length() == 0) {
            return "";
        }
        String doubled = s + s;
        int n = doubled.length();
        int start = 0, maxLen = 1;
        int[] p = new int[n];
        Arrays.fill(p, 1);
        int center = 0, right = 0;
        for (int i = 1; i < n; i++) {
            int mirror = 2 * center - i;
            if (i < right) {
                p[i] = Math.min(right - i, p[mirror]);
            }
            while (i + p[i] < n && i - p[i] >= 0 && doubled.charAt(i + p[i]) == doubled.charAt(i - p[i])) {
                p[i]++;
            }
            if (i + p[i] > right) {
                center = i;
                right = i + p[i];
            }
            if (p[i] > maxLen) {
                maxLen = p[i];
                start = i;
            }
        }
        int len = maxLen;
        int st = start - maxLen + 1;
        String res = doubled.substring(st, st + len);
        if (st >= s.length()) {
            res = res.substring(st - s.length(), st - s.length() + len);
        }
        return res;

    }
}