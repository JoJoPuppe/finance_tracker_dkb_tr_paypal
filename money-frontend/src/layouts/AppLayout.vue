<template>
  <div class="h-screen flex flex-col overflow-hidden bg-gray-900 text-white">
    <!-- Application Header -->
    <header class="bg-gray-100 py-1 px-4 flex-none border-b-1 border-b-black">
      <div class="mx-auto flex justify-between items-center">
        <h1 class="text-xl text-gray-600">Money Money Money</h1>
        
        <div class="flex items-center">
          <label class="relative cursor-pointer border border-black bg-white hover:bg-gray-600 hover:text-white hover:border-gray-600 text-black px-4 py-2 rounded-lg transition-colors duration-300 flex items-center">
            <span class="mr-2">Upload CSV</span>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
            </svg>
            <input 
              type="file" 
              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
              accept=".csv"
              @change="handleFileUpload"
            />
          </label>
          
          <!-- Toast Notification -->
          <div 
            v-if="showToast" 
            class="fixed top-5 right-5 p-4 rounded-md shadow-lg transition-all duration-500"
            :class="{ 
              'bg-green-500': toastType === 'success',
              'bg-red-500': toastType === 'error'
            }"
          >
            {{ toastMessage }}
          </div>
        </div>
      </div>
    </header>
    
    <!-- Main Content Container -->
    <div class="flex-1 bg-gray-100 w-full mx-auto flex flex-col overflow-hidden">
      <!-- Content Area -->
      <div class="flex-1 p-2 overflow-hidden">
          <slot name="rules"></slot>
      </div>
      
      <!-- Footer -->
      <footer class="flex-none text-center text-gray-400 p-2 text-sm">
        <p>© 2025 Money Money Money - Personal Finance Management</p>
      </footer>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import axios from 'axios';

export default {
  name: 'AppLayout',
  props: {
    initialActiveTab: {
      type: String,
      default: 'rules',
      validator: (value) => ['categories', 'rules', 'transactions'].includes(value)
    }
  },
  emits: ['refresh'],
  setup(props, { emit }) {
    const activeTab = ref(props.initialActiveTab);
    const showToast = ref(false);
    const toastMessage = ref('');
    const toastType = ref('success');
    
    const displayToast = (message, type = 'success') => {
      toastMessage.value = message;
      toastType.value = type;
      showToast.value = true;
      
      // Hide toast after 3 seconds
      setTimeout(() => {
        showToast.value = false;
      }, 3000);
    };
    
    const handleFileUpload = async (event) => {
      const file = event.target.files[0];
      if (!file) return;
      
      // Check if file is a CSV
      if (!file.name.endsWith('.csv')) {
        displayToast('Please select a CSV file', 'error');
        return;
      }
      
      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        // Show loading toast
        displayToast('Uploading file...', 'success');
        
        // Send to backend using axios instead of fetch
        const response = await axios.post('/api/v1/transactions/import', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        // Display success message
        displayToast(response.data.message || 'CSV file imported successfully');
        
        // Reset file input
        event.target.value = '';
        
        // Trigger refresh of parent component
        emit('refresh');
        
        // Refresh the page (optional)
        setTimeout(() => {
          window.location.reload();
        }, 1000);
        
      } catch (error) {
        console.error('Error uploading CSV:', error);
        const errorMessage = error.response?.data?.message || error.message || 'Error uploading file';
        displayToast(errorMessage, 'error');
        
        // Reset file input
        event.target.value = '';
      }
    };
    
    return {
      activeTab,
      showToast,
      toastMessage,
      toastType,
      handleFileUpload
    };
  }
};
</script>

<style scoped>
/* Any component-specific styles can go here */
</style>
