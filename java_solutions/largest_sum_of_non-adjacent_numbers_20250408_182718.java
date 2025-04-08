import java.util.Arrays;

class Solution {
    public int largestSumNonAdjacent(int[] nums) {
        if (nums == null || nums.length == 0) {
            return 0;
        }
        int n = nums.length;
        if (n == 1) {
            return Math.max(0, nums[0]);
        }
        int[] dp = new int[n];
        dp[0] = Math.max(0, nums[0]);
        dp[1] = Math.max(dp[0], Math.max(0, nums[1]));
        for (int i = 2; i < n; i++) {
            dp[i] = Math.max(dp[i - 1], dp[i - 2] + Math.max(0, nums[i]));
            dp[i] = Math.max(dp[i], Math.max(0,nums[i]));

        }
        return dp[n - 1];
    }
}