import { api } from '../utils/api.js';

const SummaryAdmin = {
  template: `
<<<<<<< Updated upstream
    <div>
      <h1>Summary Admin</h1>
      {/* Summary and analytics interface for admin */}
    </div>
  `,
=======
    <div class="container mt-4">
      <h1 class="text-center mb-4">Summary Admin</h1>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center my-5">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-2">Loading charts...</p>
      </div>

      <!-- Error State -->
      <div v-if="error" class="alert alert-danger text-center" role="alert">
        {{ error }}
        <button class="btn btn-link" @click="retryFetch">Retry</button>
      </div>

      <!-- Charts -->
      <div class="row justify-content-center g-4" v-if="!isLoading && !error">
        <!-- Auto-refresh notice -->
        <div class="col-12 text-center mb-3">
          <small class="text-muted">
            Charts auto-refresh every {{ refreshInterval / 1000 }} seconds. 
            Next refresh in {{ nextRefreshSeconds }} seconds
            <button 
              class="btn btn-sm btn-link" 
              @click="fetchCharts"
              :disabled="isRefreshing"
            >
              {{ isRefreshing ? 'Refreshing...' : 'Refresh Now' }}
            </button>
          </small>
        </div>

        <!-- Top Scores Chart -->
        <div class="col-12 col-md-6">
          <div class="card h-100">
            <div class="card-body">
              <h2 class="card-title text-center mb-3">Subject-wise Top Scores</h2>
              <div class="text-center">
                <img 
                  v-if="scoresChart"
                  :src="scoresChart" 
                  alt="Subject-wise top scores"
                  class="img-fluid" 
                  style="cursor: pointer"
                  @click="openModal('scores')"
                >
              </div>
            </div>
          </div>
        </div>

        <!-- Attempts Chart -->
        <div class="col-12 col-md-6">
          <div class="card h-100">
            <div class="card-body">
              <h2 class="card-title text-center mb-3">Subject-wise User Attempts</h2>
              <div class="text-center">
                <img 
                  v-if="attemptsChart"
                  :src="attemptsChart" 
                  alt="Subject-wise user attempts"
                  class="img-fluid" 
                  style="cursor: pointer"
                  @click="openModal('attempts')"
                >
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Chart Modal -->
      <div class="modal fade" id="chartModal" tabindex="-1">
        <div class="modal-dialog modal-lg modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">{{ modalTitle }}</h5>
              <div class="ms-auto me-2">
                <button class="btn btn-sm btn-outline-secondary me-2" @click="resetView">
                  Reset View
                </button>
                <button class="btn btn-sm btn-outline-secondary" @click="downloadChart">
                  Download
                </button>
              </div>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body text-center">
              <div class="zoom-controls mb-2">
                <button class="btn btn-sm btn-secondary me-2" @click="adjustZoom(-0.1)">-</button>
                <span>Zoom: {{ (zoomLevel * 100).toFixed(0) }}%</span>
                <button class="btn btn-sm btn-secondary ms-2" @click="adjustZoom(0.1)">+</button>
              </div>
              <div 
                class="chart-container" 
                ref="chartContainer"
                @wheel.prevent="handleWheel"
                @mousedown="startPan"
                @mousemove="pan"
                @mouseup="endPan"
                @mouseleave="endPan"
                @touchstart="handleTouchStart"
                @touchmove="handleTouchMove"
                @touchend="handleTouchEnd"
                style="overflow: hidden; position: relative; max-height: 70vh;"
              >
                <img 
                  :src="modalImage" 
                  :alt="modalTitle" 
                  class="img-fluid" 
                  ref="modalImg"
                  :style="{ 
                    transform: \`translate(\${panX}px, \${panY}px) scale(\${zoomLevel})\`,
                    transformOrigin: 'center',
                    cursor: isPanning ? 'grabbing' : 'grab'
                  }"
                >
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      isLoading: true,
      isRefreshing: false,
      error: null,
      scoresChart: null,
      attemptsChart: null,
      modalImage: null,
      modalTitle: '',
      modal: null,
      zoomLevel: 1,
      panX: 0,
      panY: 0,
      isPanning: false,
      lastX: 0,
      lastY: 0,
      refreshInterval: 30000, // 30 seconds
      lastRefreshTime: Date.now(),
      refreshTimer: null,
      touchStartX: null,
      touchStartY: null,
      initialTouchDistance: null
    }
  },
  computed: {
    nextRefreshSeconds() {
      const nextRefresh = this.refreshInterval - (Date.now() - this.lastRefreshTime);
      return Math.max(0, Math.floor(nextRefresh / 1000));
    }
  },
  methods: {
    async fetchCharts() {
      if (this.isRefreshing) return;

      this.isRefreshing = true;
      try {
        const data = await api.get('/api/charts/admin');
        this.scoresChart = data.scores_chart + '?t=' + Date.now();
        this.attemptsChart = data.attempts_chart + '?t=' + Date.now();
        this.error = null;
        this.lastRefreshTime = Date.now();
      } catch (error) {
        console.error('Error fetching charts:', error);
        this.error = 'Failed to load charts. Please try again.';
      } finally {
        this.isLoading = false;
        this.isRefreshing = false;
      }
    },
    retryFetch() {
      this.error = null;
      this.isLoading = true;
      this.fetchCharts();
    },
    setupAutoRefresh() {
      this.refreshTimer = setInterval(() => {
        this.fetchCharts();
      }, this.refreshInterval);
    },
    openModal(type) {
      if (type === 'scores') {
        this.modalImage = this.scoresChart;
        this.modalTitle = 'Subject-wise Top Scores';
      } else {
        this.modalImage = this.attemptsChart;
        this.modalTitle = 'Subject-wise User Attempts';
      }
      this.resetView();
      this.modal.show();
    },
    resetView() {
      this.zoomLevel = 1;
      this.panX = 0;
      this.panY = 0;
    },
    adjustZoom(delta) {
      const newZoom = this.zoomLevel + delta;
      if (newZoom >= 0.5 && newZoom <= 5) {
        this.zoomLevel = newZoom;
      }
    },
    handleWheel(event) {
      const container = this.$refs.chartContainer.getBoundingClientRect();
      const mouseX = event.clientX - container.left;
      const mouseY = event.clientY - container.top;
      
      const oldZoom = this.zoomLevel;
      this.zoomLevel *= event.deltaY > 0 ? 0.9 : 1.1;
      this.zoomLevel = Math.max(0.5, Math.min(5, this.zoomLevel));
      
      const scale = this.zoomLevel / oldZoom;
      const dx = mouseX - mouseX * scale;
      const dy = mouseY - mouseY * scale;
      
      this.panX = this.panX * scale + dx;
      this.panY = this.panY * scale + dy;
    },
    startPan(event) {
      this.isPanning = true;
      this.lastX = event.clientX;
      this.lastY = event.clientY;
    },
    pan(event) {
      if (!this.isPanning) return;
      
      const dx = event.clientX - this.lastX;
      const dy = event.clientY - this.lastY;
      
      this.panX += dx;
      this.panY += dy;
      
      this.lastX = event.clientX;
      this.lastY = event.clientY;
    },
    endPan() {
      this.isPanning = false;
    },
    handleTouchStart(event) {
      if (event.touches.length === 1) {
        this.touchStartX = event.touches[0].clientX;
        this.touchStartY = event.touches[0].clientY;
      } else if (event.touches.length === 2) {
        // Calculate initial distance between two fingers for pinch zoom
        const touch1 = event.touches[0];
        const touch2 = event.touches[1];
        this.initialTouchDistance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );
      }
    },
    handleTouchMove(event) {
      event.preventDefault();
      
      if (event.touches.length === 1) {
        // Pan
        const dx = event.touches[0].clientX - this.touchStartX;
        const dy = event.touches[0].clientY - this.touchStartY;
        
        this.panX += dx;
        this.panY += dy;
        
        this.touchStartX = event.touches[0].clientX;
        this.touchStartY = event.touches[0].clientY;
      } else if (event.touches.length === 2) {
        // Pinch zoom
        const touch1 = event.touches[0];
        const touch2 = event.touches[1];
        const currentDistance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );
        
        const scale = currentDistance / this.initialTouchDistance;
        this.zoomLevel = Math.max(0.5, Math.min(5, scale));
        this.initialTouchDistance = currentDistance;
      }
    },
    handleTouchEnd() {
      this.touchStartX = null;
      this.touchStartY = null;
      this.initialTouchDistance = null;
    },
    downloadChart() {
      const link = document.createElement('a');
      link.href = this.modalImage;
      link.download = `${this.modalTitle.toLowerCase().replace(/\s+/g, '-')}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  },
  mounted() {
    this.fetchCharts();
    this.setupAutoRefresh();
    this.modal = new bootstrap.Modal(document.getElementById('chartModal'));
  },
  beforeUnmount() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
  }
>>>>>>> Stashed changes
};

export default SummaryAdmin;