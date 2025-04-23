<template>
  <div class="bg-gray-800 bg-opacity-40 rounded-lg p-6 mb-6">
    <h2 class="text-xl font-semibold text-purple-300 mb-4">Search for a Record</h2>
    <div class="flex flex-col sm:flex-row gap-4 mb-4">
      <!-- Column Selection Dropdown -->
      <div class="flex-1">
        <label for="column-select" class="block text-sm font-medium text-gray-300 mb-1">Column</label>
        <select
          id="column-select"
          v-model="column"
          class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option disabled value="">Select a column</option>
          <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
        </select>
      </div>
      
      <!-- Search Input -->
      <div class="flex-1">
        <label for="search-value" class="block text-sm font-medium text-gray-300 mb-1">Search Value</label>
        <input
          id="search-value"
          v-model="value"
          type="text"
          placeholder="Enter search term"
          class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
      </div>
      
      <!-- Search Button -->
      <div class="flex items-end">
        <button
          @click="search"
          :disabled="!column || !value"
          class="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded-md transition duration-200"
        >
          Search
        </button>
      </div>
    </div>
    
    <!-- Error Message -->
    <div v-if="error" class="text-red-400 mt-2">{{ error }}</div>
  </div>
</template>

<script>
import { ref, watch } from 'vue';
import axios from 'axios';

export default {
  name: 'RuleSearch',
  props: {
    columns: {
      type: Array,
      required: true
    }
  },
  emits: ['search-result', 'search-error'],
  
  setup(props, { emit }) {
    const column = ref('');
    const value = ref('');
    const error = ref('');
    
    const search = async () => {
      error.value = '';
      emit('search-result', null);
      
      if (!column.value || !value.value) {
        error.value = 'Please select a column and enter a search value';
        return;
      }
      
      try {
        // API call to search transactions
        const response = await axios.get('/api/v1/transactions/search-by-column', {
          params: {
            column: column.value,
            value: value.value
          }
        });
        
        if (response.data.status === 'success' && response.data.data.length > 0) {
          emit('search-result', response.data.data[0]);
        } else {
          error.value = 'No matching records found';
          emit('search-error', 'No matching records found');
        }
      } catch (err) {
        console.error('Error searching for record:', err);
        error.value = err.response?.data?.message || 'Failed to search for records';
        emit('search-error', error.value);
      }
    };
    
    return {
      column,
      value,
      error,
      search
    };
  }
};
</script>