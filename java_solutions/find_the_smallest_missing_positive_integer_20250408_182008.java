import java.util.HashSet;
import java.util.Set;

class Solution {
    public int firstMissingPositive(int[] nums) {
        Set<Integer> seen = new HashSet<>();
        int max = 0;
        for (int num : nums) {
            if (num > 0) {
                seen.add(num);
                max = Math.max(max, num);
            }
        }
        for (int i = 1; i <= max + 1; i++) {
            if (!seen.contains(i)) {
                return i;
            }
        }
        return max + 1;
    }
}