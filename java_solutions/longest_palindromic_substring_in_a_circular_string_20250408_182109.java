import java.util.Arrays;

class Solution {
    public int longestPalindromeCircularString(String s) {
        int n = s.length();
        String doubled = s + s;
        int maxLen = 0;
        for (int i = 0; i < 2 * n; i++) {
            for (int j = i; j < 2 * n; j++) {
                String sub = doubled.substring(i, j + 1);
                if (isPalindrome(sub)) {
                    maxLen = Math.max(maxLen, sub.length());
                }
            }
        }
        
        if(maxLen == 0) return 0;

        
        int ans = 0;
        for(int i = 0; i < n; ++i){
            String rotated = s.substring(n-i) + s.substring(0, n-i);
            String doubledRotated = rotated + rotated;
            for(int j=0; j < 2*n; ++j){
                for(int k = j; k < 2*n; ++k){
                    String sub = doubledRotated.substring(j, k+1);
                    if(isPalindrome(sub)){
                        ans = Math.max(ans, sub.length());
                    }
                }
            }
        }
        
        
        return Math.max(maxLen, ans);
    }

    private boolean isPalindrome(String s) {
        int left = 0;
        int right = s.length() - 1;
        while (left < right) {
            if (s.charAt(left) != s.charAt(right)) {
                return false;
            }
            left++;
            right--;
        }
        return true;
    }
}