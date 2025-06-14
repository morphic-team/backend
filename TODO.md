# Backend TODO

## High Priority - Production Upgrades

### 🚀 Upgrade Image Download Strategy to best_python Approach

**Status**: Ready for implementation  
**Priority**: High  
**Impact**: +6.9% success rate improvement (54.0% → 60.9%)

**Analysis Results** (from image-download-analysis/):
- **30,383 net URLs rescued** vs 724 regressions
- **17.9% rescue rate** on failed rescuable URLs  
- **ROI validated**: 0.017 URLs gained per cost unit at 5x multiplier
- **Particularly effective against**: HTTP 403 (48.4% rescue), rate limiting (67-75% rescue)

**Implementation Tasks**:
- [ ] Update `backend/workers/image_processor.py` to use best_python strategy
- [ ] Implement sophisticated retry logic with exponential backoff
- [ ] Add browser-like headers and user agent rotation
- [ ] Configure connection pooling (pool_connections=100, pool_maxsize=100)
- [ ] Add session reuse with proper cleanup
- [ ] Implement rate limiting detection and handling
- [ ] Add comprehensive error classification and tracking
- [ ] Update background work queue to handle increased processing time
- [ ] Add monitoring for new success metrics

**Key Strategy Components**:
1. **Session Management**: Reuse HTTP sessions with proper connection pooling
2. **Header Spoofing**: Rotate user agents and browser-like headers  
3. **Retry Logic**: 3 attempts with exponential backoff (1s, 2s, 4s)
4. **Rate Limiting**: Detect 429 responses and implement backoff
5. **Error Handling**: Classify failures by stage (DNS, TCP, SSL, HTTP, content)
6. **Resource Cleanup**: Proper response cleanup to prevent memory leaks

**References**:
- See `image-download-analysis/scripts/download_test.py` BestPythonStrategy class
- Analysis results in `image-download-analysis/results/comparison_*/`
- Documentation in `image-download-analysis/docs/SUCCESS_METRICS_INTERPRETATION.md`

**Expected Results**:
- ~7% increase in successful image downloads
- Better handling of anti-bot measures (Wikimedia: 90.6% rescue rate)
- Reduced failure rates on professional stock photo sites
- Improved system reliability and user experience

---

## Future Enhancements

### 🔬 Browser Automation R&D
**Status**: Planned for after best_python deployment  
**Priority**: Medium  

Continue R&D with Playwright/Selenium-based approaches for even higher success rates on heavily protected sites.

### 📊 Production Monitoring
**Status**: Needed  
**Priority**: Medium  

Implement monitoring dashboards to track:
- Success rates by domain and error type
- Rescue effectiveness metrics  
- Performance impacts of new strategy
- ROI validation in production