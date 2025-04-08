import java.util.HashSet;
import java.util.Set;

class FindSmallestMissingPositive {
    public int firstMissingPositive(int[] nums) {
        Set<Integer> seen = new HashSet<>();
        for (int num : nums) {
            if (num > 0) {
                seen.add(num);
            }
        }
        int i = 1;
        while (seen.contains(i)) {
            i++;
        }
        return i;
    }
}