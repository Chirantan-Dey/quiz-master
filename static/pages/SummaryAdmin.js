const SummaryAdmin = {
  template: `
    <div class="container mt-4">
      <h1 class="text-center mb-4">Summary Admin</h1>

      <div class="row mb-4">
        <div class="col-12">
          <div class="card">
            <div class="card-body d-flex justify-content-between align-items-center">
              <h5 class="card-title mb-0">Data Management</h5>
              <button 
                class="btn btn-primary"
                @click="exportUserData"
                :disabled="isExporting"
              >
                {{ isExporting ? 'Exporting...' : 'Export User Data' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="exportSuccess" class="alert alert-success alert-dismissible fade show" role="alert">
        Export started! You will receive an email when it's ready.
        <button type="button" class="btn-close" @click="exportSuccess = false"></button>
      </div>

      <div v-if="error" class="alert alert-danger text-center" role="alert">
        {{ error }}
      </div>

      <div class="row justify-content-center g-4" v-if="!error">
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

      <div class="modal fade" id="chartModalAdmin" tabindex="-1">
        <div class="modal-dialog modal-lg modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">{{ modalTitle }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body text-center">
              <div 
                class="chart-container" 
                ref="chartContainer"
                @wheel.prevent="handleWheel"
                @mousedown="startPan"
                @mousemove="pan"
                @mouseup="endPan"
                @mouseleave="endPan"
                style="overflow: hidden; position: relative;"
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
      scoresChart: null,
      attemptsChart: null,
      error: null,
      modalImage: null,
      modalTitle: '',
      modal: null,
      zoomLevel: 1,
      panX: 0,
      panY: 0,
      isPanning: false,
      lastX: 0,
      lastY: 0,
      isExporting: false,
      exportSuccess: false
    }
  },
  computed: {
    isAdmin() {
      return this.$store.getters.userRoles.some(role => role.name === 'admin');
    }
  },
  methods: {
    async fetchCharts() {
      try {
        const response = await fetch('/api/charts/admin', {
          headers: {
            'Authentication-Token': this.$store.state.authToken
          }
        })
        if (!response.ok) {
          throw new Error('Failed to fetch charts')
        }
        const data = await response.json()
        this.scoresChart = data.scores_chart + '?t=' + new Date().getTime()
        this.attemptsChart = data.attempts_chart + '?t=' + new Date().getTime()
        this.error = null
      } catch (err) {
        console.error('Error fetching charts:', err)
        this.error = 'Error loading charts. Please try again later.'
      }
    },
    async exportUserData() {
      if (this.isExporting) return;
      
      this.isExporting = true;
      this.error = null;
      this.exportSuccess = false;
      
      try {
        const response = await fetch('/api/export/users', {
          method: 'POST',
          headers: {
            'Authentication-Token': this.$store.state.authToken
          }
        });
        
        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.message || 'Export failed');
        }
        
        this.exportSuccess = true;
        setTimeout(() => {
          this.exportSuccess = false;
        }, 5000);
      } catch (error) {
        console.error('Export error:', error);
        this.error = error.message || 'Error starting export';
      } finally {
        this.isExporting = false;
      }
    },
    openModal(type) {
      if (type === 'scores') {
        this.modalImage = this.scoresChart
        this.modalTitle = 'Subject-wise Top Scores'
      } else {
        this.modalImage = this.attemptsChart
        this.modalTitle = 'Subject-wise User Attempts'
      }
      this.resetView()
      this.modal.show()
    },
    resetView() {
      this.zoomLevel = 1
      this.panX = 0
      this.panY = 0
    },
    handleWheel(event) {
      const container = this.$refs.chartContainer.getBoundingClientRect()
      const mouseX = event.clientX - container.left
      const mouseY = event.clientY - container.top
      
      const oldZoom = this.zoomLevel
      this.zoomLevel *= event.deltaY > 0 ? 0.9 : 1.1
      this.zoomLevel = Math.max(0.5, Math.min(5, this.zoomLevel))
      
      const scale = this.zoomLevel / oldZoom
      const dx = mouseX - mouseX * scale
      const dy = mouseY - mouseY * scale
      
      this.panX = this.panX * scale + dx
      this.panY = this.panY * scale + dy
    },
    startPan(event) {
      this.isPanning = true
      this.lastX = event.clientX
      this.lastY = event.clientY
    },
    pan(event) {
      if (!this.isPanning) return
      
      const dx = event.clientX - this.lastX
      const dy = event.clientY - this.lastY
      
      this.panX += dx
      this.panY += dy
      
      this.lastX = event.clientX
      this.lastY = event.clientY
    },
    endPan() {
      this.isPanning = false
    }
  },
  mounted() {
    if (!this.isAdmin) {
      this.$router.push('/home-user');
      return;
    }
    
    this.fetchCharts();
    this.modal = new bootstrap.Modal(document.getElementById('chartModalAdmin'));
  }
}

export default SummaryAdmin;