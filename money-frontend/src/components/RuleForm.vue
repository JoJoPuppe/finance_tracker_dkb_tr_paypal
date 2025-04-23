<template>
  <div class="bg-gray-800 bg-opacity-40 rounded-lg">

    <div class="flex gap-x-4 items-center mb-4">
      <!-- Rule Name Input -->
      <div class="mb-6">
        <label for="rule-name" class="block text-sm font-medium text-gray-300 mb-1">Rule Name</label>
        <input
          id="rule-name"
          v-model="ruleName"
          type="text"
          placeholder="Enter rule name"
          class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
        <p v-if="validationErrors.ruleName" class="text-red-400 text-sm mt-1">{{ validationErrors.ruleName }}</p>
      </div>
  
    
      <!-- Category Selection -->
      <div class="mb-6">
        <label for="category-select" class="block text-sm font-medium text-gray-300 mb-1">Category</label>
        <select
          id="category-select"
          v-model="selectedCategory"
          class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option disabled value="">Select a category</option>
          <option v-for="category in categories" :key="category.id" :value="category.id">{{ category.name }}</option>
        </select>
        <p v-if="validationErrors.category" class="text-red-400 text-sm mt-1">{{ validationErrors.category }}</p>
      </div>
  </div>  
    <!-- Conditions Section -->
    <div class="mb-6">
      <div class="flex justify-between items-center mb-3">
        <h3 class="text-lg font-medium text-purple-200">Conditions</h3>
        <button
          @click="addCondition"
          class="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded-md text-sm flex items-center transition duration-200"
        >
          <span class="mr-1">+</span> Add Condition
        </button>
      </div>
      
      <!-- Logical Operator Selection -->
      <div class="mb-4" v-if="conditions.length > 1">
        <label class="block text-sm font-medium text-gray-300 mb-2">Connect conditions with:</label>
        <div class="flex gap-4">
          <label class="inline-flex items-center cursor-pointer">
            <input
              type="radio"
              v-model="logicalOperator"
              value="AND"
              class="form-radio h-4 w-4 text-purple-600 transition duration-150 ease-in-out"
            />
            <span class="ml-2 text-gray-300">AND</span>
            <span class="ml-1 text-gray-400 text-xs">(all conditions must match)</span>
          </label>
          
          <label class="inline-flex items-center cursor-pointer">
            <input
              type="radio"
              v-model="logicalOperator"
              value="OR"
              class="form-radio h-4 w-4 text-purple-600 transition duration-150 ease-in-out"
            />
            <span class="ml-2 text-gray-300">OR</span>
            <span class="ml-1 text-gray-400 text-xs">(any condition can match)</span>
          </label>
        </div>
      </div>
      
      <div v-if="validationErrors.conditions" class="text-red-400 text-sm mb-2">{{ validationErrors.conditions }}</div>
      
      <!-- No Conditions Message -->
      <div v-if="conditions.length === 0" class="text-gray-400 text-center py-6 bg-gray-700 bg-opacity-50 rounded-lg">
        <p>No conditions added yet</p>
        <p class="text-sm mt-1">Click "Add Condition" to create your first rule condition</p>
      </div>
      
      <!-- Condition Components -->
      <rule-condition
        v-for="(condition, index) in conditions"
        :key="index"
        :condition="condition"
        :available-columns="availableColumns"
        :cannot-remove="conditions.length === 1"
        @update="updateCondition(index, $event)"
        @remove="removeCondition(index)"
      />
    </div>
    
    <!-- Action Buttons -->
    <div class="flex justify-center space-x-4">
      <button
        v-if="editMode"
        @click="$emit('cancel-edit')"
        class="bg-gray-600 hover:bg-gray-500 text-white px-6 py-2 rounded-md transition duration-200"
      >
        Cancel
      </button>
      
      <button
        @click="submitRule"
        class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-md transition duration-200 flex items-center"
        :disabled="isSubmitting"
      >
        <span v-if="isSubmitting" class="mr-2">
          <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </span>
        {{ editMode ? 'Update Rule' : 'Create Rule' }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, watch } from 'vue';
import axios from 'axios';
import RuleCondition from './RuleCondition.vue';

export default {
  name: 'RuleForm',
  components: {
    RuleCondition
  },
  props: {
    availableColumns: {
      type: Array,
      required: true
    },
    categories: {
      type: Array,
      required: true
    },
    editRule: {
      type: Object,
      default: null
    }
  },
  emits: ['rule-created', 'rule-updated', 'cancel-edit', 'error'],
  
  setup(props, { emit }) {
    const ruleId = ref(null);
    const ruleName = ref('');
    const selectedCategory = ref('');
    const conditions = ref([{ column: '', operator: '', value: '' }]);
    const logicalOperator = ref('AND'); // Default to AND logic
    const isSubmitting = ref(false);
    const editMode = ref(false);
    
    const validationErrors = reactive({
      ruleName: '',
      category: '',
      conditions: ''
    });
    
    // Define resetForm function before using it in the watch handler
    const resetForm = () => {
      ruleId.value = null;
      ruleName.value = '';
      selectedCategory.value = '';
      conditions.value = [{ column: '', operator: '', value: '' }];
      logicalOperator.value = 'AND'; // Reset to default
      Object.keys(validationErrors).forEach(key => {
        validationErrors[key] = '';
      });
    };
    
    // Watch for changes in the editRule prop
    watch(() => props.editRule, (newRule) => {
      if (newRule) {
        // We're in edit mode
        editMode.value = true;
        ruleId.value = newRule.id;
        ruleName.value = newRule.name;
        selectedCategory.value = newRule.category_id;
        
        // Set logical operator if it exists in the rule
        logicalOperator.value = newRule.logical_operator || 'AND';
        
        // Map API condition format to local condition format
        conditions.value = newRule.conditions.map(c => ({
          column: c.field,
          operator: c.operator,
          value: c.value
        }));
        
        // If there are no conditions, add an empty one
        if (conditions.value.length === 0) {
          conditions.value.push({ column: '', operator: '', value: '' });
        }
      } else {
        // We're in create mode
        resetForm();
        editMode.value = false;
      }
    }, { immediate: true, deep: true });
    
    const addCondition = () => {
      conditions.value.push({ column: '', operator: '', value: '' });
    };
    
    const removeCondition = (index) => {
      if (conditions.value.length > 1) {
        conditions.value.splice(index, 1);
      }
    };
    
    const updateCondition = (index, updatedCondition) => {
      conditions.value[index] = updatedCondition;
    };
    
    const validateForm = () => {
      let isValid = true;
      
      // Clear previous errors
      Object.keys(validationErrors).forEach(key => {
        validationErrors[key] = '';
      });
      
      // Validate rule name
      if (!ruleName.value || ruleName.value.length < 3) {
        validationErrors.ruleName = 'Rule name must be at least 3 characters';
        isValid = false;
      } else if (!/^[a-zA-Z0-9_-]+$/.test(ruleName.value)) {
        validationErrors.ruleName = 'Rule name can only contain letters, numbers, underscores and hyphens';
        isValid = false;
      }
      
      // Validate category
      if (!selectedCategory.value) {
        validationErrors.category = 'Please select a category';
        isValid = false;
      }
      
      // Validate conditions
      let hasIncompleteCondition = false;
      conditions.value.forEach(condition => {
        if (!condition.column || !condition.operator || !condition.value) {
          hasIncompleteCondition = true;
        }
      });
      
      if (hasIncompleteCondition) {
        validationErrors.conditions = 'All condition fields must be completed';
        isValid = false;
      }
      
      return isValid;
    };
    
    const submitRule = async () => {
      if (!validateForm()) {
        return;
      }
      
      isSubmitting.value = true;
      
      try {
        const ruleData = {
          name: ruleName.value,
          category_id: selectedCategory.value,
          logical_operator: logicalOperator.value, // Include the logical operator
          conditions: conditions.value.map(c => ({
            field: c.column,
            operator: c.operator,
            value: c.value
          }))
        };
        
        let response;
        
        if (editMode.value) {
          // Update existing rule
          response = await axios.put(`/api/v1/rules/${ruleId.value}`, ruleData);
          
          if (response.data.status === 'success') {
            emit('rule-updated', response.data.data);
            resetForm();
          } else {
            emit('error', 'Failed to update rule');
          }
        } else {
          // Create new rule
          response = await axios.post('/api/v1/rules', ruleData);
          
          if (response.data.status === 'success') {
            emit('rule-created', response.data.data);
            resetForm();
          } else {
            emit('error', 'Failed to create rule');
          }
        }
      } catch (error) {
        console.error(`Error ${editMode.value ? 'updating' : 'creating'} rule:`, error);
        emit('error', error.response?.data?.message || `Failed to ${editMode.value ? 'update' : 'create'} rule`);
      } finally {
        isSubmitting.value = false;
      }
    };
    
    return {
      ruleName,
      selectedCategory,
      conditions,
      logicalOperator, // Add logical operator to the returned object
      validationErrors,
      isSubmitting,
      editMode,
      addCondition,
      removeCondition,
      updateCondition,
      submitRule
    };
  }
};
</script>