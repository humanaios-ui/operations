// Template only. No deployment or spend authorization is implied.
// Budget alerts do not stop costs or shut down resources.
// Scope covers this resource group only; shared/subscription costs can fall outside it.
// ARM budgets use the billing currency; they do not convert the amount into USD.
// Confirm the subscription bills in USD before using monthlyAmountUsd.
// Reference: https://learn.microsoft.com/en-us/azure/templates/microsoft.consumption/budgets
targetScope = 'resourceGroup'

@description('Name of the research budget in this resource group.')
@minLength(1)
param budgetName string

@description('Required positive monthly amount in USD. Use only after confirming USD billing currency. Alerts do not stop costs.')
@minValue(1)
param monthlyAmountUsd int

@description('Explicit confirmation of the actual billing currency; this parameter does not change Azure billing currency.')
@allowed(['USD'])
param confirmedBillingCurrency string

@description('ISO 8601 UTC start date, first day of month, before endDate. Follow current Azure budget date restrictions.')
@minLength(1)
param startDate string

@description('ISO 8601 UTC end date after startDate. No implicit ten-year budget lifetime.')
@minLength(1)
param endDate string

@description('Required notification recipients. Verify each address before deployment.')
@minLength(1)
@maxLength(5)
param notificationEmails array

resource researchBudget 'Microsoft.Consumption/budgets@2026-06-01' = {
  name: budgetName
  properties: {
    amount: monthlyAmountUsd
    category: 'Cost'
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: startDate
      endDate: endDate
    }
    notifications: {
      actual50: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 50
        thresholdType: 'Actual'
        contactEmails: notificationEmails
      }
      actual80: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 80
        thresholdType: 'Actual'
        contactEmails: notificationEmails
      }
      actual100: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 100
        thresholdType: 'Actual'
        contactEmails: notificationEmails
      }
      forecast100: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 100
        thresholdType: 'Forecasted'
        contactEmails: notificationEmails
      }
    }
  }
}

// Echoes the caller confirmation, not a fetched or verified billing record.
output declaredBillingCurrency string = confirmedBillingCurrency
