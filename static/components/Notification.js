const Notification = {
    template: `
        <div v-if="show"
             :class="['alert', 'alert-' + type, 'position-fixed', 'top-0', 'end-0', 'm-3']"
             style="z-index: 1050;"
             role="alert">
            {{ message }}
        </div>
    `,
    data() {
        return {
            show: false,
            message: '',
            type: 'info',
            timeout: null
        };
    },
    created() {
        this.$root.$on('show-notification', ({ type, message, duration = 3000 }) => {
            this.showNotification(type, message, duration);
        });
    },
    beforeDestroy() {
        this.$root.$off('show-notification');
        if (this.timeout) {
            clearTimeout(this.timeout);
        }
    },
    methods: {
        showNotification(type, message, duration) {
            if (this.timeout) {
                clearTimeout(this.timeout);
            }
            
            this.type = type;
            this.message = message;
            this.show = true;
            
            this.timeout = setTimeout(() => {
                this.show = false;
            }, duration);
        }
    }
};

export default Notification;