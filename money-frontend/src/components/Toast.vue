<template>
  <Transition name="toast">
    <div 
      v-if="isVisible" 
      class="fixed bottom-4 right-4 rounded-lg shadow-lg z-50 flex items-center p-4 min-w-[300px] max-w-md"
      :class="toastClasses"
    >
      <!-- Icon based on type -->
      <div class="mr-3 flex-shrink-0">
        <!-- Success Icon -->
        <svg v-if="type === 'success'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        
        <!-- Error Icon -->
        <svg v-else-if="type === 'error'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
        
        <!-- Warning Icon -->
        <svg v-else-if="type === 'warning'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        
        <!-- Info Icon (default) -->
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
        </svg>
      </div>
      
      <!-- Message -->
      <div class="flex-grow mr-2">
        <p class="text-sm font-medium">{{ message }}</p>
      </div>
      
      <!-- Close button -->
      <button 
        @click="dismiss"
        class="flex-shrink-0 p-1 rounded-full hover:bg-opacity-10 hover:bg-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-20"
        aria-label="Dismiss"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>
  </Transition>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'Toast',
  props: {
    isVisible: {
      type: Boolean,
      required: true,
    },
    message: {
      type: String,
      required: true,
    },
    type: {
      type: String,
      default: 'info',
      validator: (value) => ['success', 'error', 'warning', 'info'].includes(value),
    },
    duration: {
      type: Number,
      default: 4000, // Auto dismiss after 4 seconds by default
    },
    autoClose: {
      type: Boolean,
      default: true, // Auto close by default
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    let dismissTimer = null;
    
    // Color classes based on type
    const toastClasses = computed(() => {
      switch(props.type) {
        case 'success':
          return 'bg-green-900 text-green-100 border-l-4 border-green-500';
        case 'error':
          return 'bg-red-900 text-red-100 border-l-4 border-red-500';
        case 'warning':
          return 'bg-yellow-900 text-yellow-100 border-l-4 border-yellow-500';
        case 'info':
        default:
          return 'bg-gray-800 text-purple-100 border-l-4 border-purple-500';
      }
    });
    
    // Set timer if auto close is enabled
    if (props.isVisible && props.autoClose) {
      dismissTimer = setTimeout(() => {
        emit('close');
      }, props.duration);
    }
    
    // Close the toast
    const dismiss = () => {
      if (dismissTimer) {
        clearTimeout(dismissTimer);
      }
      emit('close');
    };
    
    return {
      toastClasses,
      dismiss,
    };
  },
};
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.toast-enter-from,
.toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>