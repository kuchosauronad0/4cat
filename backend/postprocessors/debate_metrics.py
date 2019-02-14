"""
Collapse post bodies into one long string
"""

from csv import DictReader

from backend.abstract.postprocessor import BasicPostProcessor


class DebateMetrics(BasicPostProcessor):
	"""
	Create a csv with debate metrics per thread, in addition
	to those in the `thread_metadata` postprocessor.

	op_length: length of op post (with URLs)
	op_replies: replies to the OP 
	reply_amount: posts (other than the OP) that have been replied to
	active_users: unique users with ≥ 1 posts
	reply_length: average length of a reply (without URLs)
	long_messages: 'long messages', i.e. more than 100 characters

	"""
	type = "debate_metrics"  # job type ID
	category = "Thread metrics" # category
	title = "Debate metrics"  # title displayed in UI
	description = "Collapses all posts in the results into one plain text string. The result can be used for word clouds, word trees, et cetera."  # description displayed in UI
	extension = "csv"  # extension of result file, used internally and in UI

	def process(self):
		"""
		This takes a 4CAT results file as input, and outputs a csv
		with a thread per row with its debate metrics.
		"""

		threads = {}
		reply_lengths = []

		self.query.update_status("Reading source file")
		with open(self.source_file) as source:
			csv = DictReader(source)
			for post in csv:
				if post["thread_id"] not in threads:
					print(post)
					threads[post["thread_id"]] = {
						"subject": post["subject"],
						"first_post": int(time.time()),
						"images": 0,
						"count": 0,
						"op_length": len(post["comment"])
					}

				if post["subject"]:
					threads[post["thread_id"]]["subject"] = post["subject"]

				if post["image_md5"]:
					threads[post["thread_id"]]["images"] += 1

				timestamp = int(
					post.get("unix_timestamp", datetime.datetime.fromisoformat(post["timestamp"]).timestamp))
				threads[post["thread_id"]]["first_post"] = min(timestamp, threads[post["thread_id"]]["first_post"])
				threads[post["thread_id"]]["count"] += 1

		results = [{
			"thread_id": thread_id,
			"timestamp": datetime.datetime.utcfromtimestamp(threads[thread_id]["first_post"]).strftime(
				'%Y-%m-%d %H:%M:%S'),
			"subject": threads[thread_id]["subject"],
			"num_posts": threads[thread_id]["count"],
			"num_images": threads[thread_id]["images"],
			"preview_url": "http://" + config.FlaskConfig.SERVER_NAME + "/api/4chan/pol/thread/" + str(
				thread_id) + ".json?format=html",
			"op_length": op_length,
			"op_replies": threads[thread_id]["op_length"]
			# TO DO
			# "reply_amount": ,
			# "active_users": ,
			# "reply_length": ,
			# "long_messages":
		} for thread_id in threads]

		if not results:
			return

		self.query.write_csv_and_finish(results)
