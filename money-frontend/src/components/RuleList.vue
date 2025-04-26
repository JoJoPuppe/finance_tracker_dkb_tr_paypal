<template>
  <div class="w-full pr-2">
    
    <div v-if="isLoading" class="flex justify-center items-center py-6">
      <div class="loader border-t-4 border-purple-400 rounded-full w-8 h-8 animate-spin"></div>
    </div>
    
    <div v-else-if="error" class="bg-red-900 bg-opacity-25 border border-red-500 rounded-lg p-4">
      <p class="text-red-400">{{ error }}</p>
      <button @click="fetchRules" class="text-white underline mt-2">Retry</button>
    </div>
    
    <div v-else-if="rules.length === 0" class="text-gray-600 text-center py-8">
      <p>No rules found</p>
      <p class="text-sm mt-1">Create your first rule using the form below</p>
    </div>
    
    <ul v-else class="">
      <li v-for="rule in rules" :key="rule.id" class="py-1 w-full">
        <div 
          class="items-center  rounded-md flex jusify-between"
          

        >
          <div class="w-full">
              <h3 class="text-lg text-gray-600 truncate ">{{ rule.name }}</h3>
              <p class="text-sm text-gray-400 ">
                {{ getCategoryName(rule.category_id) }} 
              </p>
          </div>
          <div class="flex space-x-1">
            <!--
            <button 
              @click.stop="$emit('revert-rule', rule.id)"
              class="text-gray-400 hover:text-yellow-400 p-1"
              title="Revert rule effects"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
              </svg>
            </button>
            -->
            <button 
              @click.stop="editRule(rule)"
              class="text-gray-400 hover:text-purple-400 p-1"
              title="Edit rule"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
              </svg>
            </button>
            <button 
              @click.stop="confirmDelete(rule)"
              class="text-gray-400 hover:text-red-400 p-1"
              title="Delete rule"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script>
import { ref, watch } from 'vue';
import axios from 'axios';

export default {
  name: 'RuleList',
  
  props: {
    categories: {
      type: Array,
      required: true
    }
  },
  
  emits: ['select-rule', 'edit-rule', 'delete-rule', 'revert-rule'],
  
  setup(props, { emit, expose }) {
    const rules = ref([]);
    const isLoading = ref(true);
    const error = ref(null);
    const selectedRuleId = ref(null);
    
    // Fetch rules when component is mounted
    const fetchRules = async () => {
      isLoading.value = true;
      error.value = null;
      
      try {
        const response = await axios.get('/api/v1/rules');
        if (response.data.status === 'success') {
          rules.value = response.data.data;
        } else {
          error.value = 'Failed to load rules';
        }
      } catch (err) {
        console.error('Error fetching rules:', err);
        error.value = 'Failed to load rules';
      } finally {
        isLoading.value = false;
      }
    };
    
    // Call fetchRules immediately
    fetchRules();
    
    // Expose refreshRules method to parent components
    expose({
      refreshRules: fetchRules
    });
    
    // Watch for new categories
    watch(() => props.categories, () => {
      // If categories change, update the rule display
      if (rules.value.length > 0) {
        rules.value = [...rules.value];
      }
    }, { deep: true });
    
    // Get category name from category ID
    const getCategoryName = (categoryId) => {
      const category = props.categories.find(cat => cat.id === categoryId);
      return category ? category.name : 'Unknown category';
    };
    
    // Select a rule
    const selectRule = (rule) => {
      selectedRuleId.value = rule.id;
      emit('select-rule', rule);
    };
    
    // Edit a rule
    const editRule = (rule) => {
      selectRule(rule);
      emit('edit-rule', rule);
    };
    
    // Confirm deletion of a rule
    const confirmDelete = (rule) => {
      if (confirm(`Are you sure you want to delete the rule "${rule.name}"?`)) {
        deleteRule(rule.id);
      }
    };
    
    // Delete a rule
    const deleteRule = async (ruleId) => {
      try {
        const response = await axios.delete(`/api/v1/rules/${ruleId}`);
        if (response.data.status === 'success') {
          // Remove the deleted rule from the list
          rules.value = rules.value.filter(rule => rule.id !== ruleId);
          
          // Reset selected rule if it was the deleted one
          if (selectedRuleId.value === ruleId) {
            selectedRuleId.value = null;
          }
          
          emit('delete-rule', ruleId);
        } else {
          emit('delete-rule', null, 'Failed to delete rule');
        }
      } catch (err) {
        console.error('Error deleting rule:', err);
        emit('delete-rule', null, err.response?.data?.message || 'Failed to delete rule');
      }
    };
    
    return {
      rules,
      isLoading,
      error,
      selectedRuleId,
      fetchRules,
      getCategoryName,
      selectRule,
      editRule,
      confirmDelete
    };
  }
};
</script>

<style scoped>
.loader {
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-top-color: #9f7aea;
}
</style>
