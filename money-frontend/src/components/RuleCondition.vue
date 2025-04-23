<template>
  <div class="bg-gray-700 p-3 rounded-lg mb-3">
    <div class="flex flex-col sm:flex-row gap-3">
      <!-- Column Selection -->
      <div class="flex-1">
        <select
          v-model="localCondition.column"
          class="w-full bg-gray-600 border border-gray-500 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          @change="updateCondition"
        >
          <option disabled value="">Select column</option>
          <option v-for="column in availableColumns" :key="column" :value="column">{{ column }}</option>
        </select>
      </div>
      
      <!-- Operator Selection -->
      <div class="flex-1">
        <select
          v-model="localCondition.operator"
          class="w-full bg-gray-600 border border-gray-500 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          @change="updateCondition"
        >
          <option disabled value="">Select operator</option>
          <option v-for="op in operators" :key="op.value" :value="op.value">{{ op.label }}</option>
        </select>
      </div>
      
      <!-- Value Input -->
      <div class="flex-1">
        <input
          v-model="localCondition.value"
          type="text"
          placeholder="Value"
          class="w-full bg-gray-600 border border-gray-500 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          @input="updateCondition"
        />
      </div>
      
      <!-- Delete Button -->
      <div class="flex items-center">
        <button
          @click="$emit('remove')"
          :disabled="cannotRemove"
          class="text-red-400 hover:text-red-300 disabled:text-gray-500 disabled:cursor-not-allowed p-2"
          :title="cannotRemove ? 'Cannot remove the only condition' : 'Remove condition'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { reactive, watch } from 'vue';

export default {
  name: 'RuleCondition',
  props: {
    condition: {
      type: Object,
      required: true
    },
    availableColumns: {
      type: Array,
      required: true
    },
    cannotRemove: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update', 'remove'],
  
  setup(props, { emit }) {
    // Create a local reactive copy of the condition
    const localCondition = reactive({
      column: props.condition.column || 'payee',
      operator: props.condition.operator || 'contains',
      value: props.condition.value || ''
    });
    
    // Define available operators
    const operators = [
      { label: 'Equal to', value: 'equal' },
      { label: 'Not equal to', value: 'not_equal' },
      { label: 'Greater than', value: 'greater_than' },
      { label: 'Less than', value: 'less_than' },
      { label: 'Contains', value: 'contains' },
      { label: 'Starts with', value: 'starts_with' },
      { label: 'Ends with', value: 'ends_with' },
      { label: 'Matches regex', value: 'regex' },
      { label: 'In list', value: 'in' }
    ];
    
    // Watch for changes in the incoming condition props
    watch(() => props.condition, (newCondition) => {
      localCondition.column = newCondition.column || 'payee';
      localCondition.operator = newCondition.operator || 'contains';
      localCondition.value = newCondition.value || '';
    }, { deep: true });
    
    // Function to emit changes to parent
    const updateCondition = () => {
      emit('update', {
        column: localCondition.column,
        operator: localCondition.operator,
        value: localCondition.value
      });
    };
    
    return {
      localCondition,
      operators,
      updateCondition
    };
  }
};
</script>