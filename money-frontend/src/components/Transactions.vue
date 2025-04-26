<template>
  <div class="h-full flex flex-col">
    
    <!-- Category Selection -->
    <div class="mb-4">
      <div class="flex gap-x-3 w-2/3 items-center">
        <Multiselect
          v-model="selectedCategoryId"
          :options="sortedCategoryOptions"
          :searchable="true"
          placeholder="Select a category"
          label="label"
          valueProp="value"
          class="category-select flex-grow"
        />
        <button 
          @click="loadTransactions"
          :disabled="!selectedCategoryId || isLoading"
          class="bg-purple-600 cursor-pointer hover:bg-purple-700 text-white font-medium px-4 py-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="isLoading">
            <span class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2 align-middle"></span>
            Loading...
          </span>
          <span v-else>Submit</span>
        </button>
        <div class="w-full">
          <div class="relative w-full">
            <input
              id="search-input"
              v-model="searchQuery"
              @input="onSearchInput"
              type="text"
              placeholder="Search by payee, payer, purpose..."
              class="w-full bg-gray-200 border border-gray-600 pl-10 pr-3 py-2 text-grey-600 focus:outline-none focus:ring-2 focus:ring-gray-400"
            />
            <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-600">
              <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
            <div v-if="isSearching" class="absolute inset-y-0 right-0 flex items-center pr-3">
              <span class="inline-block w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></span>
            </div>
          </div>
          <p v-if="searchQuery && searchQuery.length > 0 && searchQuery.length < minSearchChars" class="mt-1 text-xs text-gray-600">
            Enter at least {{ minSearchChars }} characters to search
          </p>
        </div>
      </div>
    </div>
    
    <!-- Search Transactions -->
    
    <!-- Batch Update Category Section (shown when transactions are selected) -->
    <div v-if="selectedTransactions.length > 0" class="py-3 ">
      <div class="flex items-center justify-between">
        <span class="text-gray-600 font-medium">{{ selectedTransactions.length }} transaction(s) selected</span>
        <button @click="clearSelection" class="text-gray-600 hover:text-gray-900 text-sm underline">Clear selection</button>
      </div>
      
      <div class="mt-3 flex gap-x-3">
        <Multiselect
          v-model="batchCategoryId"
          :options="sortedBatchCategoryOptions"
          :searchable="true"
          placeholder="Select a category"
          label="label"
          valueProp="value"
          class="category-select flex-grow"
        />
        <button 
          @click="updateSelectedTransactionsCategory"
          :disabled="!batchCategoryId || isUpdating"
          class="bg-purple-600 hover:bg-purple-700 text-white font-medium px-4 py-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="isUpdating">
            <span class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2 align-middle"></span>
            Updating...
          </span>
          <span v-else>Update</span>
        </button>
      </div>
    </div>
    
    <!-- Error Display -->
    <div v-if="error" class="bg-red-900 bg-opacity-25 border border-red-500 rounded-lg p-4 mb-4">
      <p class="text-red-400">{{ error }}</p>
      <button @click="loadTransactions" class="text-gray-600 underline mt-2">Retry</button>
    </div>
    
    <!-- Results Display -->
    <div v-if="transactions.length > 0" class="flex-1 flex flex-col overflow-hidden">
      <h3 class="text-lg font-medium text-gray-600 mb-2">
        {{ getCategoryName(selectedCategoryId) }} - {{ transactions.length }} transaction(s)
        <span v-if="hasMoreToLoad" class="text-sm text-gray-400 ml-2">(Scroll to load more)</span>
      </h3>
      
      <!-- Transactions Table with fixed height and scroll -->
      <div class="overflow-x-auto overflow-y-auto flex-1" ref="tableContainer" @scroll="handleScroll">
        <table class="min-w-full overflow-hidden text-gray-800">
          <thead>
            <tr class="bg-gray-600 sticky top-0 z-10">
              <th class="px-4 py-2 text-center text-xs font-medium text-gray-300 uppercase tracking-wider w-16">
                <div 
                  @click="toggleAllTransactions"
                  class="flex items-center justify-center h-8 w-8 mx-auto cursor-pointer transition-colors"
                  :class="areAllTransactionsSelected ? 'bg-gray-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-500'"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Date</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Amount</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Payee</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Payer</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Purpose</th>
              <th class="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Hash</th>
            </tr>
          </thead>
          <tbody class="">
            <tr v-for="tx in transactions" :key="tx.id" 
                class="hover:bg-gray-200 cursor-pointer"
                :class="{'bg-gray-400': isTransactionSelected(tx.id)}">
              <td class="px-4 py-3 text-center">
                <div 
                  @click.stop="toggleTransactionSelection(tx.id)"
                  class="flex items-center justify-center h-8 w-8 mx-auto cursor-pointer transition-colors"
                  :class="isTransactionSelected(tx.id) ? 'bg-black text-white' : 'text-gray-400 hover:bg-gray-500'"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </td>
              <td class="px-4 py-3" @click="toggleTransactionSelection(tx.id)">{{ tx.value_date || 'N/A' }}</td>
              <td class="px-4 py-3 whitespace-nowrap" :class="tx.amount >= 0 ? 'text-green-400' : 'text-red-400'" @click="toggleTransactionSelection(tx.id)">
                {{ formatCurrency(tx.amount) }}
              </td>
              <td class="px-4 py-3" @click="toggleTransactionSelection(tx.id)">{{ tx.payee || 'N/A' }}</td>
              <td class="px-4 py-3" @click="toggleTransactionSelection(tx.id)">{{ tx.payer || 'N/A' }}</td>
              <td class="px-4 py-3" @click="toggleTransactionSelection(tx.id)">
                <div class="max-w-xs">
                  {{ tx.purpose || 'N/A' }}
                </div>
              </td>
              <td class="px-4 py-3">{{ tx.transaction_hash || 'N/A' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Loading Indicator at Bottom -->
      <div v-if="isLoadingMore" class="text-center py-3 text-gray-300">
        <span class="inline-block w-5 h-5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin mr-2 align-middle"></span>
        Loading more transactions...
      </div>
      
      <!-- End of Results Indicator -->
      <div v-if="!hasMoreToLoad && transactions.length > initialLoadCount" class="text-center py-3 text-gray-400">
        End of transactions
      </div>
    </div>
    
    <div v-else-if="hasSearched && !isLoading" class="text-center py-8 text-gray-400">
      <p>No transactions found for this category</p>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue';
import axios from 'axios';
import debounce from 'lodash.debounce';
import Multiselect from '@vueform/multiselect';

export default {
  name: 'Transactions',
  
  components: {
    Multiselect
  },
  
  props: {
    categories: {
      type: Array,
      required: true
    },
    refreshTrigger: {
      type: Number,
      default: 0
    }
  },
  
  setup(props) {
    const selectedCategoryId = ref('no-category'); // Set default to "no-category"
    const transactions = ref([]);
    const isLoading = ref(false);
    const isLoadingMore = ref(false);
    const error = ref(null);
    const hasSearched = ref(false);
    const currentPage = ref(1);
    const hasMoreToLoad = ref(true);
    const initialLoadCount = 25;
    const tableContainer = ref(null);
    const loadThreshold = 0.8; // Load more when scrolled 80% of the container
    
    // Batch update functionality
    const selectedTransactions = ref([]);
    const batchCategoryId = ref('');
    const isUpdating = ref(false);
    
    // Search functionality
    const searchQuery = ref('');
    const isSearching = ref(false);
    const minSearchChars = 3;
    const isSearchMode = ref(false); // Flag to track if we're in search mode
    
    // Create sorted category options
    const sortedCategoryOptions = computed(() => {
      // Start with the "no-category" option
      const options = [
        { value: 'no-category', label: 'Transactions with no category' }
      ];
      
      // Sort categories alphabetically by name
      const sortedCategories = [...props.categories].sort((a, b) => {
        return a.name.localeCompare(b.name);
      });
      
      // Add sorted categories
      sortedCategories.forEach(category => {
        options.push({
          value: category.id,
          label: category.name
        });
      });
      
      return options;
    });
    
    // Create sorted batch category options
    const sortedBatchCategoryOptions = computed(() => {
      // Start with the "remove category" option
      const options = [
        { value: 'null', label: 'Remove category' }
      ];
      
      // Sort categories alphabetically by name
      const sortedCategories = [...props.categories].sort((a, b) => {
        return a.name.localeCompare(b.name);
      });
      
      // Add sorted categories
      sortedCategories.forEach(category => {
        options.push({
          value: category.id,
          label: category.name
        });
      });
      
      return options;
    });
    
    // Check if a transaction is selected
    const isTransactionSelected = (id) => {
      return selectedTransactions.value.includes(id);
    };
    
    // Toggle selection for a transaction
    const toggleTransactionSelection = (id) => {
      const index = selectedTransactions.value.indexOf(id);
      if (index === -1) {
        selectedTransactions.value.push(id);
      } else {
        selectedTransactions.value.splice(index, 1);
      }
    };
    
    // Select or deselect all transactions
    const areAllTransactionsSelected = computed(() => {
      return transactions.value.length > 0 && 
             transactions.value.every(tx => selectedTransactions.value.includes(tx.id));
    });
    
    // Toggle all transactions selection
    const toggleAllTransactions = () => {
      if (areAllTransactionsSelected.value) {
        // Deselect all transactions from the current view
        transactions.value.forEach(tx => {
          const index = selectedTransactions.value.indexOf(tx.id);
          if (index !== -1) {
            selectedTransactions.value.splice(index, 1);
          }
        });
      } else {
        // Select all transactions from the current view
        transactions.value.forEach(tx => {
          if (!selectedTransactions.value.includes(tx.id)) {
            selectedTransactions.value.push(tx.id);
          }
        });
      }
    };
    
    // Clear selection
    const clearSelection = () => {
      selectedTransactions.value = [];
    };
    
    // Update category for selected transactions
    const updateSelectedTransactionsCategory = async () => {
      if (selectedTransactions.value.length === 0 || !batchCategoryId.value) return;
      
      isUpdating.value = true;
      error.value = null;
      
      try {
        const updates = [];
        
        // Process all selected transactions
        for (const txId of selectedTransactions.value) {
          // Convert 'null' string to actual null for removing categories
          const categoryId = batchCategoryId.value === 'null' ? null : parseInt(batchCategoryId.value);
          
          // Update category for each transaction
          await axios.put(`/api/v1/transactions/${txId}/category`, { 
            category_id: categoryId 
          });
          
          updates.push(txId);
        }
        
        // Clear selection after successful update
        selectedTransactions.value = [];
        batchCategoryId.value = '';
        
        // Reload transactions to reflect the changes
        await loadTransactions();
        
      } catch (err) {
        console.error('Error updating transaction categories:', err);
        error.value = err.response?.data?.message || 'Failed to update transaction categories';
      } finally {
        isUpdating.value = false;
      }
    };
    
    // Get category name by ID
    const getCategoryName = (categoryId) => {
      if (categoryId === 'no-category') {
        return 'Transactions with no category';
      }
      const category = props.categories.find(cat => cat.id === Number(categoryId));
      return category ? category.name : 'Unknown category';
    };
    
    // Format currency
    const formatCurrency = (amount) => {
      return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR',
      }).format(amount);
    };
    
    // Check if we need to load more data because viewport is larger than content
    const checkInitialViewportSize = () => {
      if (!tableContainer.value || !hasMoreToLoad.value || isLoadingMore.value) return;
      
      const { scrollHeight, clientHeight } = tableContainer.value;
      
      // If the container doesn't have a scrollbar (content fits in viewport)
      // and we have exactly the initial count of transactions, load more
      if (scrollHeight <= clientHeight && transactions.value.length === initialLoadCount && hasMoreToLoad.value) {
        console.log("Initial content fits viewport, automatically loading more transactions");
        loadMoreTransactions();
      }
    };
    
    // Fetch initial transactions for the selected category
    const loadTransactions = async () => {
      if (!selectedCategoryId.value) return;
      
      isLoading.value = true;
      error.value = null;
      currentPage.value = 1;
      transactions.value = [];
      hasMoreToLoad.value = true;
      isSearchMode.value = false; // Reset search mode when loading regular transactions
      
      // Clear selection when loading new transactions
      selectedTransactions.value = [];
      
      try {
        await fetchTransactionsPage(1);
        hasSearched.value = true;
        
        // Check if we need to load more because the initial data fits in viewport
        setTimeout(checkInitialViewportSize, 100); // Small delay to ensure DOM has updated
      } catch (err) {
        console.error('Error fetching transactions:', err);
        error.value = err.response?.data?.message || 'Failed to load transactions';
        transactions.value = [];
        hasMoreToLoad.value = false;
      } finally {
        isLoading.value = false;
      }
    };
    
    // Fetch transactions page
    const fetchTransactionsPage = async (page) => {
      let url;
      if (selectedCategoryId.value === 'no-category') {
        url = '/api/v1/transactions/uncategorized';
      } else {
        url = `/api/v1/transactions/by-category/${selectedCategoryId.value}`;
      }
      
      const response = await axios.get(url, {
        params: {
          page: page,
          per_page: initialLoadCount
        }
      });
      
      if (response.data.status === 'success') {
        const newTransactions = response.data.data.transactions;
        transactions.value = [...transactions.value, ...newTransactions];
        
        // Check if there are more pages to load
        const pagination = response.data.data.pagination;
        hasMoreToLoad.value = pagination.page < pagination.total_pages;
        currentPage.value = pagination.page;
      } else {
        throw new Error('Failed to load transactions');
      }
    };
    
    // Load more transactions when scrolling
    const loadMoreTransactions = async () => {
      if (!hasMoreToLoad.value || isLoadingMore.value) return;
      
      isLoadingMore.value = true;
      try {
        if (isSearchMode.value) {
          // If in search mode, use the search endpoint with the next page
          await fetchMoreSearchResults(currentPage.value + 1);
        } else {
          // Otherwise use the regular endpoint
          await fetchTransactionsPage(currentPage.value + 1);
        }
      } catch (err) {
        console.error('Error loading more transactions:', err);
        error.value = 'Failed to load more transactions';
      } finally {
        isLoadingMore.value = false;
      }
    };
    
    // Fetch more search results
    const fetchMoreSearchResults = async (page) => {
      try {
        const response = await axios.get('/api/v1/transactions/search', {
          params: {
            q: searchQuery.value,
            page: page,
            per_page: initialLoadCount,
            category_id: selectedCategoryId.value !== '' ? selectedCategoryId.value : undefined
          }
        });
        
        if (response.data.status === 'success') {
          const newTransactions = response.data.data.transactions;
          transactions.value = [...transactions.value, ...newTransactions];
          
          // Update pagination info
          const pagination = response.data.data.pagination;
          hasMoreToLoad.value = pagination.page < pagination.total_pages;
          currentPage.value = pagination.page;
        } else {
          throw new Error('Failed to fetch more search results');
        }
      } catch (err) {
        console.error('Error fetching more search results:', err);
        throw err;
      }
    };
    
    // Handle scroll event to load more transactions
    const handleScroll = () => {
      if (!tableContainer.value || !hasMoreToLoad.value || isLoadingMore.value) return;
      
      const { scrollTop, scrollHeight, clientHeight } = tableContainer.value;
      const scrollPosition = scrollTop + clientHeight;
      const scrollThreshold = scrollHeight * loadThreshold;
      
      // Debug logging to help troubleshoot scroll issues
      console.log('Scroll detected:', {
        scrollPosition,
        scrollThreshold,
        difference: scrollPosition - scrollThreshold,
        shouldLoad: scrollPosition >= scrollThreshold
      });
      
      if (scrollPosition >= scrollThreshold) {
        loadMoreTransactions();
      }
    };
    
    // Load uncategorized transactions by default when component mounts
    onMounted(() => {
      loadTransactions();
      
      // Ensure scroll event listener is properly attached after component is mounted
      if (tableContainer.value) {
        tableContainer.value.addEventListener('scroll', handleScroll);
      }
      
      // Add window resize listener to handle viewport size changes
      window.addEventListener('resize', checkInitialViewportSize);
    });
    
    // Clean up event listeners when component is unmounted
    onUnmounted(() => {
      if (tableContainer.value) {
        tableContainer.value.removeEventListener('scroll', handleScroll);
      }
      window.removeEventListener('resize', checkInitialViewportSize);
    });
    
    // Watch for refresh trigger changes (when a rule is applied)
    const watchRefreshTrigger = computed(() => props.refreshTrigger);
    
    // Watch for changes to the refresh trigger
    const watchOptions = { immediate: false };
    watch(watchRefreshTrigger, () => {
      loadTransactions();
    }, watchOptions);
    
    // Handle search input with debouncing
    const onSearchInput = debounce(async () => {
      if (!searchQuery.value || searchQuery.value.length < minSearchChars) {
        if (searchQuery.value.length === 0) {
          // If search is cleared, reload the default transactions
          loadTransactions(); // This will also reset isSearchMode to false
        }
        return;
      }
      
      isSearching.value = true;
      isSearchMode.value = true; // Set search mode when performing a search
      error.value = null;
      currentPage.value = 1;
      transactions.value = [];
      hasMoreToLoad.value = true;
      
      try {
        // Use the dedicated search endpoint
        const response = await axios.get('/api/v1/transactions/search', {
          params: {
            q: searchQuery.value,
            page: 1,
            per_page: initialLoadCount,
            category_id: selectedCategoryId.value !== '' ? selectedCategoryId.value : undefined
          }
        });
        
        if (response.data.status === 'success') {
          transactions.value = response.data.data.transactions;
          
          // Update pagination info
          const pagination = response.data.data.pagination;
          hasMoreToLoad.value = pagination.page < pagination.total_pages;
          currentPage.value = pagination.page;
        } else {
          throw new Error('Failed to search transactions');
        }
        
        hasSearched.value = true;
        
        // Check if we need to load more because the initial data fits in viewport
        setTimeout(checkInitialViewportSize, 100); // Small delay to ensure DOM has updated
      } catch (err) {
        console.error('Error searching transactions:', err);
        error.value = err.response?.data?.message || 'Failed to search transactions';
        transactions.value = [];
        hasMoreToLoad.value = false;
      } finally {
        isSearching.value = false;
      }
    }, 300); // 300ms debounce delay
    
    return {
      selectedCategoryId,
      transactions,
      isLoading,
      isLoadingMore,
      error,
      hasSearched,
      hasMoreToLoad,
      tableContainer,
      getCategoryName,
      formatCurrency,
      loadTransactions,
      handleScroll,
      initialLoadCount,
      // Batch update functionality
      selectedTransactions,
      batchCategoryId,
      isUpdating,
      isTransactionSelected,
      toggleTransactionSelection,
      areAllTransactionsSelected,
      toggleAllTransactions,
      clearSelection,
      updateSelectedTransactionsCategory,
      // Search functionality
      searchQuery,
      isSearching,
      minSearchChars,
      onSearchInput,
      // Sorted category options
      sortedCategoryOptions,
      sortedBatchCategoryOptions
    };
  }
};
</script>

<style src="@vueform/multiselect/themes/default.css"></style>

<style scoped>
.transactions-container {
  height: 400px;
  overflow-y: auto;
  position: relative;
}


.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Customize multiselect to match our theme */
:deep(.multiselect) {
  --ms-bg: rgb(55, 65, 81);
  --ms-border-color: rgb(75, 85, 99);
  --ms-border-width: 1px;
  --ms-radius: 0.0rem;
  --ms-py: 0.5rem;
  
  /* Dropdown */
  --ms-dropdown-bg: rgb(31, 41, 55);
  --ms-dropdown-border-color: rgb(75, 85, 99);
  --ms-dropdown-border-width: 1px;
  
  /* Options */
  --ms-option-bg-pointed: rgb(75, 85, 99);
  --ms-option-color-pointed: rgb(255, 255, 255);
  --ms-option-bg-selected: rgb(124, 58, 237);
  --ms-option-color-selected: white;
  --ms-option-bg-selected-pointed: rgb(109, 40, 217);
  --ms-option-color-selected-pointed: white;
  --ms-option-bg-disabled: rgb(55, 65, 81);
  --ms-option-color-disabled: rgb(156, 163, 175);
  
  /* Tags */
  --ms-tag-bg: rgb(124, 58, 237);
  --ms-tag-color: white;
  --ms-tag-border-width: 0px;
  --ms-tag-radius: 0.0rem;
  --ms-tag-font-weight: 500;
  
  /* Search */
  --ms-search-color: white;
  --ms-search-bg: rgb(31, 41, 55);
}

:deep(.multiselect-placeholder),
:deep(.multiselect-single-label),
:deep(.multiselect-multiple-label) {
  color: #f1f1f1;
}

:deep(.multiselect-search) {
  color: white;
}

:deep(.multiselect-dropdown) {
  color: #f1f1f1;
  max-height: 250px;
}

:deep(.multiselect-clear) {
  color: rgb(156, 163, 175);
}

:deep(.multiselect-spinner) {
  color: rgb(124, 58, 237);
}
</style>
