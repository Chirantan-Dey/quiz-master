const SummaryUser = {
  template: `
    <div class="container mt-4">
      <h1 class="text-center mb-4">Summary User</h1>
      <div v-if="error" class="alert alert-danger text-center" role="alert">
        {{ error }}
      </div>
      <div class="row justify-content-center g-4" v-if="!error">
        <div class="col-12 col-md-6">
          <div class="card h-100">
            <div class="card-body">
              <h2 class="card-title text-center mb-3">Questions by Subject</h2>
              <div class="text-center">
                <img 
                  v-if="questionsChart"
                  :src="questionsChart" 
                  alt="Subject-wise question count"
                  class="img-fluid" 
                  style="cursor: pointer"
                  @click="openModal('questions')"
                >
              </div>
            </div>
          </div>
        </div>
        <div class="col-12 col-md-6">
          <div class="card h-100">
            <div class="card-body">
              <h2 class="card-title text-center mb-3">Your Attempts by Subject</h2>
              <div class="text-center">
                <img 
                  v-if="attemptsChart"
                  :src="attemptsChart" 
                  alt="Your subject-wise attempts"
                  class="img-fluid" 
                  style="cursor: pointer"
                  @click="openModal('attempts')"
                >
                <div v-if="noAttempts" class="alert alert-info mt-3">
                  Take some quizzes to see your attempt statistics
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal fade" id="chartModalUser" tabindex="-1">
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
      questionsChart: null,
      attemptsChart: null,
      error: null,
      noAttempts: false,
      modalImage: null,
      modalTitle: '',
      modal: null,
      zoomLevel: 1,
      panX: 0,
      panY: 0,
      isPanning: false,
      lastX: 0,
      lastY: 0
    }
  },
  methods: {
    async fetchCharts() {
      try {
        const response = await fetch('/api/charts/user', {
          headers: {
            'Authentication-Token': this.$store.state.authToken
          }
        })
        if (!response.ok) {
          if (response.status === 404) {
            this.noAttempts = true
            return
          }
          throw new Error('Failed to fetch charts')
        }
        const data = await response.json()
        this.questionsChart = data.questions_chart + '?t=' + new Date().getTime()
        this.attemptsChart = data.attempts_chart + '?t=' + new Date().getTime()
        this.error = null
        this.noAttempts = false
      } catch (err) {
        console.error('Error fetching charts:', err)
        this.error = 'Error loading charts. Please try again later.'
      }
    },
    openModal(type) {
      if (type === 'questions') {
        this.modalImage = this.questionsChart
        this.modalTitle = 'Questions by Subject'
      } else {
        this.modalImage = this.attemptsChart
        this.modalTitle = 'Your Attempts by Subject'
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
    this.fetchCharts()
    this.modal = new bootstrap.Modal(document.getElementById('chartModalUser'))
  }
}

export default SummaryUser