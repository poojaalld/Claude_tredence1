const sendEmail = async (message) => {
  console.log(`Sending "${message}" to the mailing list...`);
};

function scheduleEmail(message) {
  console.log("Queueing message:", message);
  await sendEmail(message);
}

scheduleEmail("Weekly stand-up reminder");
