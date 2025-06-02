// Enhanced custom functions for Event Management load testing

module.exports = {
  // Generate realistic event data with phase-aware variations
  generateEventData: function(context, events, done) {
    const eventTypes = [
      'Tech Conference 2025', 'Annual Music Festival', 'Art Gallery Opening', 'Business Leadership Summit',
      'International Sports Tournament', 'Culinary Food Festival', 'Cultural Heritage Event', 'Professional Workshop',
      'Industry Networking Mixer', 'Product Launch Showcase', 'Skills Training Bootcamp', 'Charity Fundraising Gala',
      'Innovation Symposium', 'Startup Pitch Competition', 'Academic Research Conference', 'Community Celebration'
    ];
    const venues = [
      'Grand Convention Center', 'Metropolitan City Hall', 'Olympic Stadium Complex', 'Luxury Hotel Ballroom',
      'University Main Campus', 'Downtown Community Center', 'Riverside Park Pavilion', 'Historic Theater District',
      'Modern Art Museum', 'Corporate Conference Center', 'International Exhibition Hall', 'Scenic Outdoor Amphitheater',
      'Innovation Hub Facility', 'Cultural Arts Complex', 'Sports Arena', 'Waterfront Event Space'
    ];
    const cities = [
      'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX', 
      'Phoenix, AZ', 'Philadelphia, PA', 'San Antonio, TX', 'San Diego, CA',
      'Dallas, TX', 'Austin, TX', 'Jacksonville, FL', 'Fort Worth, TX',
      'Columbus, OH', 'Indianapolis, IN', 'Charlotte, NC', 'San Francisco, CA'
    ];
    const currentTime = new Date().getTime();
    const testStartTime = context.vars.$testStartTime || currentTime;
    const elapsedMinutes = Math.floor((currentTime - testStartTime) / (1000 * 60));

    // PHASE LOGIC: (30/20/25/30/15)
    let phasePrefix = '';
    let ticketMultiplier = 1;
    if (elapsedMinutes < 30) {
      phasePrefix = '[Medium-1]';
      ticketMultiplier = 1.2;
    } else if (elapsedMinutes < 50) {
      phasePrefix = '[Light-1]';
      ticketMultiplier = 0.8;
    } else if (elapsedMinutes < 75) {
      phasePrefix = '[Heavy]';
      ticketMultiplier = 2.0;
    } else if (elapsedMinutes < 105) {
      phasePrefix = '[Medium-2]';
      ticketMultiplier = 1.2;
    } else {
      phasePrefix = '[Light-2]';
      ticketMultiplier = 0.8;
    }

    const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)];
    const venue = venues[Math.floor(Math.random() * venues.length)];
    const city = cities[Math.floor(Math.random() * cities.length)];
    const futureDate = new Date();
    const daysAhead = Math.floor(Math.random() * 90) + 7;
    futureDate.setDate(futureDate.getDate() + daysAhead);
    const baseTickets = eventType.includes('Stadium') || eventType.includes('Festival') ? 1000 : 200;
    const ticketCount = Math.floor((baseTickets + Math.random() * 500) * ticketMultiplier);

    context.vars.eventDescription = `${phasePrefix} ${eventType} - LoadTest Event ${Math.floor(Math.random() * 100000)}`;
    context.vars.eventDate = futureDate.toISOString().split('T')[0];
    context.vars.ticketNumber = ticketCount;
    context.vars.additionalNotes = `Phase: ${phasePrefix} | Generated: ${new Date().toISOString()} | Contact: loadtest-${Math.floor(Math.random() * 1000)}@example.com | Capacity: ${ticketCount}`;
    context.vars.eventPlace = `${venue}, ${city}`;
    return done();
  },

  // Generate update data with realistic modifications
  generateUpdateData: function(context, events, done) {
    const updateReasons = [
      'Venue upgraded due to overwhelming demand',
      'Additional premium tickets now available',
      'Celebrity guest speaker confirmed',
      'Schedule extended with bonus sessions',
      'Major sponsorship partnership announced',
      'VIP package options added',
      'Early bird pricing extended',
      'Accessibility improvements completed',
      'Live streaming option added',
      'Catering menu enhanced'
    ];
    const reason = updateReasons[Math.floor(Math.random() * updateReasons.length)];
    const ticketIncrease = Math.floor(Math.random() * 150) + 25; // 25-175 additional tickets

    context.vars.updatedDescription = context.vars.eventDescription + ` - UPDATED: ${reason}`;
    context.vars.updatedTickets = context.vars.ticketNumber + ticketIncrease;
    context.vars.updatedNotes = `UPDATED: ${reason} | Previous capacity: ${context.vars.ticketNumber} | New capacity: ${context.vars.updatedTickets} | Updated: ${new Date().toISOString()}`;

    return done();
  },

  // Generate bulk event data for database stress testing
  generateBulkEventData: function(context, events, done) {
    const bulkTypes = [
      'Workshop Series', 'Training Bootcamp', 'Certification Program', 
      'Masterclass Collection', 'Conference Track', 'Seminar Series'
    ];
    const batchIdentifiers = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta'];
    const bulkType = bulkTypes[Math.floor(Math.random() * bulkTypes.length)];
    const batchId = batchIdentifiers[Math.floor(Math.random() * batchIdentifiers.length)];
    const bulkDate = new Date();
    bulkDate.setDate(bulkDate.getDate() + Math.floor(Math.random() * 30) + 15);

    context.vars.bulkEventDescription = `Bulk ${bulkType} - Batch ${batchId} Series ${Math.floor(Math.random() * 10000)}`;
    context.vars.bulkEventDate = bulkDate.toISOString().split('T')[0];
    context.vars.bulkTicketNumber = Math.floor(Math.random() * 300) + 100; // 100-400 tickets
    context.vars.bulkEventPlace = `Load Test Facility ${Math.floor(Math.random() * 100)}, Training Center Complex`;

    return done();
  },

  // CPU-intensive operations to trigger HPA scaling
  cpuStressTest: function(context, events, done) {
    const startTime = Date.now();
    let result = 0;
    const iterations = Math.floor(Math.random() * 75000) + 25000; // 25k-100k iterations

    for (let i = 0; i < iterations; i++) {
      result += Math.sqrt(i) * Math.sin(i / 100) * Math.cos(i / 50);
      if (i % 1000 === 0) {
        for (let j = 2; j < 100; j++) {
          let isPrime = true;
          for (let k = 2; k <= Math.sqrt(j); k++) {
            if (j % k === 0) {
              isPrime = false;
              break;
            }
          }
          if (isPrime) result += j;
        }
      }
    }

    // Memory allocation stress
    const largeArray = new Array(Math.floor(Math.random() * 10000) + 5000);
    for (let i = 0; i < largeArray.length; i++) {
      largeArray[i] = {
        id: i,
        data: Math.random().toString(36).substring(2, 15),
        timestamp: Date.now(),
        computed: Math.sqrt(i) * Math.PI
      };
    }

    const endTime = Date.now();
    const executionTime = endTime - startTime;
    context.vars.cpuResult = result;
    context.vars.cpuExecutionTime = executionTime;
    context.vars.cpuIterations = iterations;
    context.vars.memoryAllocated = largeArray.length;

    if (Math.random() < 0.1) {
      console.log(`[CPU-STRESS] Executed ${iterations} iterations in ${executionTime}ms, allocated ${largeArray.length} objects`);
    }
    return done();
  },

  // Enhanced phase logging with detailed information (matching new timings)
  logPhaseInfo: function(context, events, done) {
    const timestamp = new Date().toISOString();
    const testStartTime = context.vars.$testStartTime || Date.now();
    const elapsedMinutes = Math.floor((Date.now() - testStartTime) / (1000 * 60));

    let currentPhase = 'Unknown';
    let expectedLoad = 'N/A';
    let expectedPods = 'N/A';

    if (elapsedMinutes < 30) {
      currentPhase = 'Phase 1: Medium Load';
      expectedLoad = '45-55 RPS';
      expectedPods = '3-5 pods, 2-3 nodes';
    } else if (elapsedMinutes < 50) {
      currentPhase = 'Phase 2: Light Load';
      expectedLoad = '10 RPS';
      expectedPods = '1-2 pods, 1-2 nodes';
    } else if (elapsedMinutes < 75) {
      currentPhase = 'Phase 3: Heavy Load';
      expectedLoad = '90-110 RPS';
      expectedPods = '8-12 pods, 4-6 nodes';
    } else if (elapsedMinutes < 105) {
      currentPhase = 'Phase 4: Medium Load';
      expectedLoad = '45-55 RPS';
      expectedPods = '3-5 pods, 2-3 nodes';
    } else {
      currentPhase = 'Phase 5: Light Load';
      expectedLoad = '10 RPS';
      expectedPods = '1-2 pods, 1-2 nodes';
    }

    if (Math.random() < 0.05) {
      console.log(`[${timestamp}] ${currentPhase} | Elapsed: ${elapsedMinutes}min | Expected: ${expectedLoad} → ${expectedPods}`);
    }
    context.vars.currentPhase = currentPhase;
    context.vars.elapsedMinutes = elapsedMinutes;
    context.vars.expectedLoad = expectedLoad;
    return done();
  },

  // Dynamic think time based on load phase and user behavior
  dynamicThinkTime: function(context, events, done) {
    const elapsedMinutes = context.vars.elapsedMinutes || 0;
    let baseThinkTime = 2000; // 2 seconds base
    let variationRange = 3000; // 0-3 seconds variation

    if (elapsedMinutes < 30 || (elapsedMinutes >= 75 && elapsedMinutes < 105)) {
      // Medium load phases - normal user behavior
      baseThinkTime = 2500;
      variationRange = 4000;
    } else if (elapsedMinutes < 50 || elapsedMinutes >= 105) {
      // Light load phases - users taking more time
      baseThinkTime = 4000;
      variationRange = 6000;
    } else if (elapsedMinutes >= 50 && elapsedMinutes < 75) {
      // Heavy load phase - faster user interactions
      baseThinkTime = 1000;
      variationRange = 2000;
    }

    const thinkTime = baseThinkTime + (Math.random() * variationRange);
    context.vars.dynamicThinkTime = Math.floor(thinkTime);
    return done();
  },

  // Memory stress test for database and application servers
  memoryStressTest: function(context, events, done) {
    const startTime = Date.now();
    const memoryStressData = [];
    const objectCount = Math.floor(Math.random() * 5000) + 2000; // 2k-7k objects

    for (let i = 0; i < objectCount; i++) {
      memoryStressData.push({
        id: `stress_test_${i}_${Date.now()}`,
        eventData: {
          title: `Memory Stress Event ${i}`,
          description: 'A'.repeat(Math.floor(Math.random() * 500) + 100),
          attendees: new Array(Math.floor(Math.random() * 50) + 10).fill(null).map((_, idx) => ({
            id: idx,
            name: `Attendee_${idx}_${Math.random().toString(36).substring(2, 8)}`,
            email: `test${idx}@example.com`,
            registered: new Date().toISOString()
          })),
          metadata: {
            created: new Date().toISOString(),
            tags: ['load-test', 'memory-stress', `phase-${Math.floor(Math.random() * 5) + 1}`],
            settings: {
              notifications: true,
              reminders: Math.floor(Math.random() * 5),
              priority: Math.floor(Math.random() * 10)
            }
          }
        },
        computedValues: new Array(100).fill(null).map((_, idx) => Math.random() * idx),
        timestamp: Date.now()
      });
    }

    const totalSize = memoryStressData.reduce((sum, item) => sum + JSON.stringify(item).length, 0);
    const avgAttendees = memoryStressData.reduce((sum, item) => sum + item.eventData.attendees.length, 0) / memoryStressData.length;
    const endTime = Date.now();

    context.vars.memoryObjectsCreated = objectCount;
    context.vars.memoryTotalSize = totalSize;
    context.vars.memoryAvgAttendees = Math.floor(avgAttendees);
    context.vars.memoryExecutionTime = endTime - startTime;
    memoryStressData.length = 0;

    return done();
  },

  // Enhanced error handler with phase-aware logging
  handleError: function(context, events, done) {
    const error = context.vars.$error;
    const currentPhase = context.vars.currentPhase || 'Unknown Phase';
    const elapsedMinutes = context.vars.elapsedMinutes || 0;

    if (error) {
      console.error(`[ERROR] ${new Date().toISOString()} | ${currentPhase} (${elapsedMinutes}min) | ${error.message || 'Unknown error'}`);
      context.vars.errorPhase = currentPhase;
      context.vars.errorTime = elapsedMinutes;
    }
    return done();
  },

  // Initialize test start time for phase calculations
  initializeTest: function(context, events, done) {
    if (!context.vars.$testStartTime) {
      context.vars.$testStartTime = Date.now();
      console.log(`[INIT] Load test initialized at ${new Date().toISOString()}`);
    }
    return done();
  },

  // Generate realistic search queries for database stress
  generateSearchQuery: function(context, events, done) {
    const searchTerms = [
      'conference', 'workshop', 'festival', 'seminar', 'training',
      'networking', 'exhibition', 'summit', 'bootcamp', 'masterclass'
    ];
    const locations = [
      'New York', 'California', 'Texas', 'Florida', 'Chicago',
      'Boston', 'Seattle', 'Denver', 'Atlanta', 'Phoenix'
    ];
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    const searchType = Math.random();
    let searchQuery = '';

    if (searchType < 0.4) {
      searchQuery = searchTerms[Math.floor(Math.random() * searchTerms.length)];
    } else if (searchType < 0.7) {
      searchQuery = locations[Math.floor(Math.random() * locations.length)];
    } else {
      searchQuery = months[Math.floor(Math.random() * months.length)];
    }
    context.vars.searchQuery = searchQuery;
    context.vars.searchPage = Math.floor(Math.random() * 5);
    context.vars.searchSize = [10, 20, 50][Math.floor(Math.random() * 3)];
    return done();
  }
};
