# Cache Duration Update Plan

## Current State Analysis

### Cache Configuration Locations
1. extensions.py (default configuration)
   - CACHE_DEFAULT_TIMEOUT: Changed to 1 (was 3)

2. app.py (application configuration)
   - CACHE_DEFAULT_TIMEOUT = 3

3. views.py (specific endpoints)
   - get_subjects(): timeout=3
   - get_quizzes(): timeout=1
   - get_admin_charts(): timeout=7
   - get_user_charts(): timeout=7

4. resources.py (API resources)
   - subject_list: timeout=10
   - quiz_list: timeout=10
   - chapter_list: timeout=10
   - questions: timeout=1800
   - scores: timeout=1800

## Required Changes

### Phase 1: Update Default Configurations
1. ✓ extensions.py: CACHE_DEFAULT_TIMEOUT = 1
2. app.py: Update CACHE_DEFAULT_TIMEOUT to 1

### Phase 2: Standardize View Caching
In views.py:
1. Update get_subjects() to timeout=1
2. get_quizzes() is already at timeout=1
3. Update get_admin_charts() to timeout=1
4. Update get_user_charts() to timeout=1

### Phase 3: Update Resource Caching
In resources.py:
1. Update subject_list cache to timeout=1
2. Update quiz_list cache to timeout=1
3. Update chapter_list cache to timeout=1
4. Update questions cache to timeout=1
5. Update scores cache to timeout=1

## Implementation Order
1. ✓ Update extensions.py default timeout
2. Update app.py configuration
3. Update views.py timeouts
4. Update resources.py timeouts
5. Test each endpoint after updates

## Testing Plan
1. Verify Redis server is running
2. Test each endpoint to ensure cache invalidation works:
   - Subject listing and operations
   - Quiz listing and operations
   - Question operations
   - Score operations
   - Admin and user charts
3. Monitor application performance
4. Verify data consistency across all endpoints

## Notes
- All caches will be standardized to 1 second timeout for consistency
- Cache invalidation logic remains unchanged
- May need to monitor system performance due to increased cache operations