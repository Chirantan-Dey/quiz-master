export const OfflineMixin = {
    data() {
        return {
            isOffline: !navigator.onLine
        };
    },
    created() {
        window.addEventListener('online', this.updateOnlineStatus);
        window.addEventListener('offline', this.updateOnlineStatus);
    },
    destroyed() {
        window.removeEventListener('online', this.updateOnlineStatus);
        window.removeEventListener('offline', this.updateOnlineStatus);
    },
    methods: {
        updateOnlineStatus() {
            this.isOffline = !navigator.onLine;
            if (this.isOffline) {
                // Show offline notification
                this.$root.$emit('show-notification', {
                    type: 'warning',
                    message: 'You are offline. Some features may be limited.'
                });
            } else {
                // Show back online notification
                this.$root.$emit('show-notification', {
                    type: 'success',
                    message: 'You are back online!'
                });
            }
        }
    },
    computed: {
        canPerformAction() {
            return !this.isOffline;
        }
    }
};