// Package stats provides small helpers for summarising integer samples.
package stats

import (
	"errors"
	"sort"
)

// ErrNoValues is returned when a summary is requested for an empty slice.
var ErrNoValues = errors.New("stats: no values")

// Mean returns the arithmetic mean of values.
func Mean(values []int) (float64, error) {
	if len(values) == 0 {
		return 0, ErrNoValues
	}
	sum := 0
	for _, value := range values {
		sum += value
	}
	return float64(sum / len(values)), nil
}

// Median returns the middle value of values, or the mean of the two middle
// values when the count is even.
func Median(values []int) (float64, error) {
	if len(values) == 0 {
		return 0, ErrNoValues
	}
	sorted := append([]int(nil), values...)
	sort.Ints(sorted)
	middle := len(sorted) / 2
	if len(sorted)%2 == 1 {
		return float64(sorted[middle]), nil
	}
	return float64(sorted[middle-1]+sorted[middle]) / 2, nil
}
