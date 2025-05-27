// Custom functions for Event Management load testing

module.exports = {
  // Generate realistic event data
  generateEventData: function(context, events, done) {
    const eventTypes = [
      'Tech Conference', 'Music Festival', 'Art Exhibition', 'Business Seminar',
      'Sports Tournament', 'Food Festival', 'Cultural Event', 'Workshop',
      'Networking Event', 'Product Launch', 'Training Session', 'Charity Gala'
    ];
    
    const places = [
      'Convention Center', 'City Hall', 'Stadium', 'Hotel Ballroom',
      'University Campus', 'Community Center', 'Park Pavilion', 'Theater',
      'Museum', 'Conference Room', 'Exhibition Hall', 'Outdoor Venue'
    ];
    
    const cities = [
      'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
      'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'Austin'
    ];
    
    // Generate random event data
    const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)];
    const place = places[Math.floor(Math.random() * places.length)];
    const city = cities[Math.floor(Math.random() * cities.length)];
    
    // Generate future date (1-90 days from now)
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + Math.floor(Math.random() * 90) + 1);
    
    context.vars.eventDescription = `${eventType} - Load Test Event ${Math.floor(Math.random() * 10000)}`;
    context.vars.eventDate = futureDate.toISOString().split('T')[0]; // YYYY-MM-DD format
    context.vars.ticketNumber = Math.floor(Math.random() * 500) + 50; // 50-550 tickets
    context.vars.additionalNotes = `Generated during load test at ${new Date().toISOString()}. Contact: test@example.com`;
    context.vars.eventPlace = `${place}, ${city}`;
    
    return done();
  },
  
  // Generate update data for existing events
  generateUpdateData: function(context, events, done) {
    const updateReasons = [
      'Venue changed due to high demand',
      'Additional tickets available',
      'Special guest speaker confirmed',
      'Schedule update',
      'Sponsorship announcement'
    ];
    
    const reason = updateReasons[Math.floor(Math.random() * updateReasons.length)];
    
    context.vars.updatedDescription = context.vars.eventDescription + ` - UPDATED: ${reason}`;
    context.vars.updatedTickets = context.vars.ticketNumber + Math.floor(Math.random() * 100);
    
    return done();
  },
  
  // Generate bulk event data for stress testing
  generateBulkEventData: function(context, events, done) {
    const bulkSuffixes = ['Batch A', 'Batch B', 'Batch C', 'Series 1', 'Series 2'];
    const suffix = bulkSuffixes[Math.floor(Math.random() * bulkSuffixes.length)];
    
    // Generate date for bulk events (near future)
    const bulkDate = new Date();
    bulkDate.setDate(bulkDate.getDate() + Math.floor(Math.random() * 30) + 1);
    
    context.vars.bulkEventDescription = `Bulk Load Test Event ${suffix} - ${Math.floor(Math.random() * 1000)}`;
    context.vars.bulkEventDate = bulkDate.toISOString().split('T')[0];
    context.vars.bulkTicketNumber = Math.floor(Math.random() * 200) + 100; // 100-300 tickets
    context.vars.bulkEventPlace = `Load Test Venue ${Math.floor(Math.random() * 50)}`;
    
    return done();
  },
  
  // Simulate CPU-intensive operations
  cpuStressTest: function(context, events, done) {
    // Perform CPU-intensive calculations
    let result = 0;
    const iterations = 50000;
    
    for (let i = 0; i < iterations; i++) {
      result += Math.sqrt(i) * Math.sin(i) * Math.cos(i);
    }
    
    context.vars.cpuResult = result;
    return done();
  },
  
  // Log phase information
  logPhaseInfo: function(context, events, done) {
    const phase = context.vars.$phase || 'Unknown Phase';
    const timestamp = new Date().toISOString();
    
    console.log(`[${timestamp}] Current Phase: ${phase}`);
    console.log(`[${timestamp}] Target: https://hamzakalech.com`);
    
    return done();
  },
  
  // Generate realistic user think times based on phase
  dynamicThinkTime: function(context, events, done) {
    // Vary think time based on load phase
    const baseThinkTime = 2000; // 2 seconds base
    const variation = Math.random() * 3000; // 0-3 seconds variation
    
    const thinkTime = baseThinkTime + variation;
    context.vars.dynamicThinkTime = Math.floor(thinkTime);
    
    return done();
  },
  
  // Custom error handler
  handleError: function(context, events, done) {
    const error = context.vars.$error;
    if (error) {
      console.error(`[ERROR] ${new Date().toISOString()}: ${error.message}`);
    }
    return done();
  }
};
