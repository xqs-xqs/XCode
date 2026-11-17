package stats

import (
	"errors"
	"testing"
)

func TestMean(t *testing.T) {
	cases := []struct {
		name   string
		values []int
		want   float64
	}{
		{"whole", []int{2, 4, 6}, 4},
		{"fraction", []int{1, 2}, 1.5},
		{"negative fraction", []int{-1, -2, -2}, -5.0 / 3.0},
	}
	for _, tc := range cases {
		got, err := Mean(tc.values)
		if err != nil {
			t.Fatalf("%s: unexpected error %v", tc.name, err)
		}
		if got != tc.want {
			t.Errorf("%s: Mean(%v) = %v, want %v", tc.name, tc.values, got, tc.want)
		}
	}
}

func TestMeanEmpty(t *testing.T) {
	if _, err := Mean(nil); !errors.Is(err, ErrNoValues) {
		t.Fatalf("Mean(nil) error = %v, want ErrNoValues", err)
	}
}

func TestMedian(t *testing.T) {
	if got, _ := Median([]int{5, 1, 3}); got != 3 {
		t.Errorf("Median odd = %v, want 3", got)
	}
	if got, _ := Median([]int{4, 1, 3, 2}); got != 2.5 {
		t.Errorf("Median even = %v, want 2.5", got)
	}
}
